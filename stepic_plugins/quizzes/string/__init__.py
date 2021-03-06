import re
import textwrap

from codejail import safe_exec

from stepic_plugins.base import BaseQuiz
from stepic_plugins.exceptions import FormatError
from stepic_plugins.executable_base import JailedCodeFailed, run
from stepic_plugins.schema import attachment
from stepic_plugins.utils import attachment_content, create_attachment, normalize_text


class StringQuiz(BaseQuiz):
    name = 'string'

    class Schemas:
        source = {
            'pattern': str,
            'case_sensitive': bool,
            'use_re': bool,
            'match_substring': bool,
            'code': str  # TODO: make solve() optional
        }
        # TODO: Use voluptuous library for schema definition and validation.
        #       Make `files` optional with the default value to not break
        #       quiz submissions in the mobile apps.
        reply = {
            'text': str,
            'files': [attachment],
        }

    def __init__(self, source):
        super().__init__(source)
        self.pattern = source.pattern
        self.case_sensitive = source.case_sensitive
        self.use_re = source.use_re
        self.match_substring = source.match_substring
        self.code = source.code
        self.use_code = self._is_code_used()
        if self.use_re:
            try:
                r = re.compile(self.pattern)
            # catching Exception and not re.error because compile can throw
            # not only re.error (ex pattern = '()'*100)
            except Exception:
                raise FormatError('Malformed regular expression')

            if r.match(''):
                raise FormatError('Pattern matches empty sting')

    def async_init(self):
        if self.use_code:
            try:
                answer = self.run_edyrun('solve', data={})
            except JailedCodeFailed as e:
                raise FormatError(str(e))
            reply = {
                'text': answer,
                'files': [],
            }
            score, hint = self.check(reply, '', throw=True)
            if score != 1:
                hint = '\nHint: {}'.format(hint) if hint else ''
                raise FormatError('score of answer is {score} instead of 1.{hint}'.format(
                    score=score,
                    hint=hint))
        return None

    def clean_reply(self, reply, dataset):
        if len(reply.files) > 1:
            raise FormatError("More than one file is submitted")
        # TODO: Add file content normalization here after download links on attachments in
        # reply is implemented. Currently normalization is performed only on check. Learners
        # download their original attached files.
        return reply

    def check(self, reply, clue, throw=False):
        if reply['files']:
            file_content = attachment_content(reply['files'][0])
            text = normalize_text(file_content.decode(errors='replace'))
        else:
            # Text here comes normalized by the serializer in raid app
            text = reply['text']
        if self.use_code:
            return self.check_using_code(text, clue, throw=throw)
        elif self.use_re:
            return self.check_re(text)
        else:
            return self.check_simple(text)

    def _is_code_used(self):
        for line in self.code.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                return True
        return False

    def check_using_code(self, text, clue, throw=False):
        try:
            score, hint = self.run_edyrun('score', data=(text, clue))
            return score, hint
        except (JailedCodeFailed, ValueError, TypeError) as e:
            if throw:
                raise JailedCodeFailed(str(e))
            return False

    def check_re(self, text):
        """Run re.match in sandbox, because re.match('(x+x+)+y', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        is to resource consuming.

        May be should use https://code.google.com/p/re2/ here.
        """
        if self.match_substring:
            pattern = "{0}({1}){0}".format(r"(.|\n)*", self.pattern)
        else:
            pattern = self.pattern
        global_dict = {'matched': False,
                       'pattern': pattern,
                       'text': text}
        code = textwrap.dedent("""
                import re
                match = re.match(pattern, text, {flags})
                matched = match.group() == text if match else False
                """).format(flags='' if self.case_sensitive else 'flags=re.I')
        try:
            safe_exec.safe_exec(code, global_dict)
        except safe_exec.SafeExecException:
            score = False
        else:
            score = bool(global_dict['matched'])
        return score

    def check_simple(self, text):
        if self.case_sensitive:
            pattern = self.pattern
        else:
            text = text.lower()
            pattern = self.pattern.lower()

        if self.match_substring:
            score = pattern in text
        else:
            score = pattern == text
        return score

    def run_edyrun(self, command, data=None, **kwargs):
        files = []
        return run(command, self.code, data, files, **kwargs)

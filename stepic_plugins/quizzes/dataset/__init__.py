import random

from stepic_plugins import settings
from stepic_plugins.base import BaseQuiz
from stepic_plugins.constants import WARNING_NEWLINE, WARNING_SPLIT_LINES
from stepic_plugins.exceptions import PluginError, FormatError
from stepic_plugins.executable_base import JailedCodeFailed, run


class DatasetQuiz(BaseQuiz):
    name = 'dataset'

    class Schemas:
        source = {
            'code': str
        }
        reply = {
            'file': str
        }
        dataset = {
            'file': str
        }

    def __init__(self, source):
        super().__init__(source)
        self.code = source.code

    def async_init(self):
        def check_sample():
            try:
                self.run_edyrun('test')
            except JailedCodeFailed as e:
                raise FormatError(str(e))

        def check_random():
            try:
                dataset, clue = self.generate()
                reply = self.run_edyrun('solve', data=dataset,
                                        output_limit=settings.DATASET_QUIZ_SIZE_LIMIT)
                score, hint = self.check(reply, clue, throw=True)
            except JailedCodeFailed as e:
                raise FormatError(str(e))
            if score != 1:
                hint = '\nHint: {}'.format(hint) if hint else ''
                raise FormatError('score of answer is {score} instead of 1.{hint}'.format(
                    score=score,
                    hint=hint))
            return dataset

        random_dataset = check_random()
        check_sample()

        try:
            sample_dataset, sample_output = self.run_edyrun('sample')
        except JailedCodeFailed as e:
            raise FormatError(str(e))

        samples = []
        if sample_dataset or sample_output:
            samples.append((sample_dataset, sample_output))
        return {
            'options': {
                'time_limit': 5 * 60,
                'samples': samples,
            },
            'warnings': self._generate_warnings(samples, random_dataset['file']),
        }

    def _generate_warnings(self, samples, random_dataset):
        warnings = []
        for dataset, _ in samples + [(random_dataset, None)]:
            if dataset and not dataset.endswith('\n'):
                warnings.append(WARNING_NEWLINE)
                break
        for pattern in [r".split('\n')", r'.split("\n")']:
            if pattern in self.code:
                warnings.append(WARNING_SPLIT_LINES)
                break
        return warnings

    def clean_reply(self, reply, dataset):
        return reply.file.strip()

    def check(self, reply, clue, throw=False):
        try:
            score, hint = self.run_edyrun('score', data=(reply, clue))
            return score, hint
        except (JailedCodeFailed, ValueError, TypeError) as e:
            if throw:
                raise JailedCodeFailed(str(e))
            return False

    def generate(self):
        seed = random.randrange(10 ** 9)
        try:
            dataset, clue = self.run_edyrun('generate', seed=seed,
                                            output_limit=settings.DATASET_QUIZ_SIZE_LIMIT)

            if not (isinstance(dataset, dict) and 'file' in dataset and isinstance(dataset['file'], str)):
                raise TypeError("Bad dataset")
            return dataset, clue
        except (JailedCodeFailed, ValueError, TypeError) as e:
            raise PluginError(str(e))

    def run_edyrun(self, command, data=None, **kwargs):
        files = []
        return run(command, self.code, data, files, **kwargs)

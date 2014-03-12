App.DatasetQuizComponent = Em.Component.extend
  is_dataset_downloaded: false

  init: ->
    @_super()
    if not @get('reply')?
      @set 'reply',
        text: ''

  is_input_disabled: (->
    @get('disabled') or not @get('is_dataset_downloaded')
  ).property('disabled', 'is_dataset_downloaded')

  didInsertElement: ->
    @$('.get_dataset').click =>
      @get('controller').send 'download_started'
    # @focus()
    @_super.apply(@, arguments)


  actions:
    download_started: ->
      @set 'is_dataset_downloaded', true

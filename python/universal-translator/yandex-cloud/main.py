from translation import detect_lang, translate, lang_to_code, is_like_russian

INTRO_TEXT = 'Привет! Вы находитесь в приватном навыке "Универсальный переводчик". ' \
    'Скажите, какое слово вы хотите перевести с какого на какой язык.' \
    'Чтобы выйти, скажите "Хватит".'


def do_translate(form, translate_state):
    api_req = {
        'text': form['slots'].get('phrase', {}).get('value'),
        'lang_from': form['slots'].get('from', {}).get('value'),
        'lang_to': form['slots'].get('to', {}).get('value'),            
    }
    api_req = {k: v for k, v in api_req.items() if v}
    if 'lang_from' in api_req:
        code = lang_to_code(api_req['lang_from'])
        if not code:
            return 'Не поняла, на какой язык переводить', translate_state
        api_req['lang_from'] = code
    if 'lang_to' in api_req:
        code = lang_to_code(api_req['lang_to'])
        if not code:
            return 'Не поняла, c какого языка переводить', translate_state
        api_req['lang_to'] = code
    translate_state.update(api_req)
    if 'text' not in translate_state:
        return 'Не поняла, какой текст нужно перевести', translate_state
    if is_like_russian(translate_state['text']) and 'lang_to' not in translate_state:
        return 'На какой язык нужно перевести?', translate_state
    if not is_like_russian(translate_state['text']) and 'lang_from' not in translate_state:
        return 'С какого языка нужно перевести?', translate_state
    tran_error, tran_result = translate(**translate_state)
    text = tran_error or tran_result
    return text, translate_state


def handler(event, context):
    translate_state = event.get('state', {}).get('session', {}).get('translate', {})
    last_phrase = event.get('state', {}).get('session', {}).get('last_phrase')
    intents = event.get('request', {}).get('nlu', {}).get('intents', {})
    command = event.get('request', {}).get('command')

    text = INTRO_TEXT
    end_session = 'false'

    translate_main = intents.get('translate_main')
    translate_ellipsis = intents.get('translate_ellipsis')
    if intents.get('exit'):
        text = 'Приятно было попереводить для вас! Чтобы вернуться в навык, скажите "Запусти навык Универсальный переводчик". До свидания!'
        end_session = 'true'
    elif intents.get('YANDEX.HELP'):
        text = INTRO_TEXT
    elif intents.get('YANDEX.REPEAT'):
        if last_phrase:
            text = last_phrase
        else:
            text = 'Ох, я забыла, что нужно повторить. Попросите меня лучше что-нибудь перевести.'
    elif translate_main:
        text, translate_state = do_translate(translate_main, translate_state)
    elif translate_ellipsis:
        text, translate_state = do_translate(translate_ellipsis, translate_state)
    elif command:
        text = 'Не поняла вас. Чтобы выйти из навыка "Универсальный переводчик", скажите "Хватит".'

    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            'text': text,
            'end_session': end_session
        },
        'session_state': {'translate': translate_state, 'last_phrase': text}
    }

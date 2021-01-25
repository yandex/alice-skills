import enum
import inspect
import sys
from abc import ABC, abstractmethod
from typing import Optional

from kremlin_tour import intents
from kremlin_tour.request import Request
from kremlin_tour.response_helpers import (
    GEOLOCATION_ALLOWED,
    GEOLOCATION_REJECTED,
    button,
    has_location,
    image_gallery,
)
from kremlin_tour.state import STATE_RESPONSE_KEY


class Place(enum.Enum):
    UNKNOWN = 1
    TOWER = 2
    CATHEDRAL = 3

    @classmethod
    def from_request(cls, request: Request, intent_name: str):
        slot = request.intents[intent_name]['slots']['place']['value']
        if slot == 'tower':
            return cls.TOWER
        elif slot == 'cathedral':
            return cls.CATHEDRAL
        else:
            return cls.UNKNOWN


def move_to_place_scene(request: Request, intent_name: str):
    place = Place.from_request(request, intent_name)
    if place == Place.TOWER:
        return Tower()
    elif place == Place.CATHEDRAL:
        return Cathedral()
    else:
        return UnknownPlace()


class Scene(ABC):

    @classmethod
    def id(cls):
        return cls.__name__

    """Генерация ответа сцены"""
    @abstractmethod
    def reply(self, request):
        raise NotImplementedError()

    """Проверка перехода к новой сцене"""
    def move(self, request: Request):
        next_scene = self.handle_local_intents(request)
        if next_scene is None:
            next_scene = self.handle_global_intents(request)
        return next_scene

    @abstractmethod
    def handle_global_intents(self):
        raise NotImplementedError()

    @abstractmethod
    def handle_local_intents(request: Request) -> Optional[str]:
        raise NotImplementedError()

    def fallback(self, request: Request):
        return self.make_response('Извините, я вас не поняла. Пожалуйста, попробуйте переформулировать вопрос.')

    def make_response(self, text, tts=None, card=None, state=None, buttons=None, directives=None):
        response = {
            'text': text,
            'tts': tts if tts is not None else text,
        }
        if card is not None:
            response['card'] = card
        if buttons is not None:
            response['buttons'] = buttons
        if directives is not None:
            response['directives'] = directives
        webhook_response = {
            'response': response,
            'version': '1.0',
            STATE_RESPONSE_KEY: {
                'scene': self.id(),
            },
        }
        if state is not None:
            webhook_response[STATE_RESPONSE_KEY].update(state)
        return webhook_response


class KremlinTourScene(Scene):

    def handle_global_intents(self, request):
        if intents.START_TOUR in request.intents: 
            return StartTour()
        elif intents.START_TOUR_WITH_PLACE in request.intents:
            return move_to_place_scene(request, intents.START_TOUR_WITH_PLACE)


class Welcome(KremlinTourScene):
    def reply(self, request: Request):
        text = ('Добро пожаловать на экскурсию по кремлю Великого Новгорода. '
            'Тут я расскажу вам исторю башен кремя и собора. Но прежде дайте дайте доступ к геолокации, '
            'чтобы я понимала, где вы находитесь.')
        directives = {'request_geolocation': {}}
        return self.make_response(text, buttons=[
            button('Расскажи экскурсию', hide=True),
        ], directives=directives)

    def handle_local_intents(self, request: Request):
        print('request type: ' + request.type)
        if request.type in (
            GEOLOCATION_ALLOWED, 
            GEOLOCATION_REJECTED,
        ):
            return HandleGeolocation()


class StartTour(KremlinTourScene):
    def reply(self, request: Request):
        text = 'Вы в Великом Новгороде, на территории старинного кремля. Возле какого места вы находитесь?'
        return self.make_response(text, state={
            'screen': 'start_tour'
        }, buttons=[
            button('Спасская башня'),
            button('Софийский собор'),
        ])

    def handle_local_intents(self, request: Request):
        if intents.START_TOUR_WITH_PLACE_SHORT:
            return move_to_place_scene(request, intents.START_TOUR_WITH_PLACE_SHORT)


class Tower(KremlinTourScene):
    def reply(self, request: Request):
        tts = ('Спасская башня. Спасская башня — проездная башня Новгородского детинца, строение конца XV века. '
            'Башня шестиярусная, в плане представляет собой вытянутый прямоугольник 15 × 8,3 м.'
            'Ширина проезда — 3 м. Высота стен — 19 м, а толщина стен на уровне второго яруса — 2 м.'
        )
        return self.make_response(
            text='',
            tts=tts,
            card=image_gallery(image_ids=[
                '213044/6d63099949494a74d4a0',
                '997614/89f90bf8bca41f92c85c',
            ])
        )

    def handle_local_intents(self, request: Request):
        pass


class Cathedral(KremlinTourScene):
    def reply(self, request: Request):
        return self.make_response(text='В будущем здесь появится рассказ о Софийском соборе')

    def handle_local_intents(self, request: Request):
        pass


class HandleGeolocation(KremlinTourScene):
    def reply(self, request: Request):
        if request.type == GEOLOCATION_ALLOWED:
            location = request['session']['location']
            lat = location['lat']
            lon = location['lon']
            text = f'Ваши координаты: широта {lat}, долгота {lon}'
            return self.make_response(text)
        else:
            text = 'К сожалению, мне не удалось получить ваши координаты. Чтобы продолжить работу с навыком'
            return self.make_response(text, directives={'request_geolocation': {}})        

    def handle_local_intents(self, request: Request):
        pass


def _list_scenes():
    current_module = sys.modules[__name__]
    scenes = []
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and issubclass(obj, Scene):
            scenes.append(obj)
    return scenes


SCENES = {
    scene.id(): scene for scene in _list_scenes()
}

DEFAULT_SCENE = Welcome

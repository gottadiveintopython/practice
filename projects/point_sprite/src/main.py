from kivy.config import Config
Config.set('graphics', 'maxfps', 0)
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
import asynckivy


KV_CODE = '''
BoxLayout:
    padding: 10
    spacing: 10
    BoxLayout:
        id: anim_list
        orientation: 'vertical'
        size_hint_x: .2
        spacing: 10
    RelativeLayout:
        id: where_anim_plays
        Label:
            id: fps_label
            color: 0, 0, 0, 1
            outline_width: 3
            outline_color: 1, 1, 1, 1
            font_size: 30
'''


class SampleApp(App):
    def build(self):
        return Builder.load_string(KV_CODE)
    def on_start(self):
        root = self.root

        def _keep_showing_fps():
            fps_label = root.ids.fps_label
            def update_label(*__):
                fps = Clock.get_fps()
                fps_label.text = f"{fps:.01f}fps"
            Clock.schedule_interval(update_label, 1)
        _keep_showing_fps()

        def _load_anim_list():
            def on_state(button, state):
                from importlib import import_module
                try:
                    button.coro.close()
                except AttributeError:
                    pass
                if state == 'down':
                    mod = import_module('.' + button.text, 'point_sprite')
                    coro = mod.animation(
                        root.ids.where_anim_plays,
                        # max_sprites=10000,
                        # max_spawn_interval=0,  # 0 means spawns every frame
                        # color='#FFFFFF66',
                        # max_velocity_y=20,
                        # pointsize=32,
                        # image=r'data/logo/kivy-icon-64.png',
                    )
                    asynckivy.start(coro)
                    button.coro = coro
            anim_list = root.ids.anim_list
            module_names = (
                'ver_py_array',
                'ver_py_numpy',
            )
            for name in module_names:
                button = Factory.ToggleButton(
                    text=name,
                    group='sprite_anim',
                    font_size='20sp',
                    outline_width=1,
                    outline_color=(0, 0, 0, 1),
                )
                button.bind(state=on_state)
                anim_list.add_widget(button)
        _load_anim_list()
SampleApp().run()

from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.appbar import MDActionBottomAppBarButton

KV = '''
#:import MDActionBottomAppBarButton kivymd.uix.appbar.MDActionBottomAppBarButton


MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDBottomAppBar:
        id: bottom_appbar
        action_items:
            [
            MDActionBottomAppBarButton(icon="gmail"),
            MDActionBottomAppBarButton(icon="bookmark"),
            ]

        MDFabBottomAppBarButton:
            icon: "plus"
            on_release: app.change_actions_items()
'''


class Example(MDApp):
    def change_actions_items(self):
        self.root.ids.bottom_appbar.action_items = [
            MDActionBottomAppBarButton(icon="magnify"),
            MDActionBottomAppBarButton(icon="trash-can-outline"),
            MDActionBottomAppBarButton(icon="download-box-outline"),
        ]

    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)


Example().run()
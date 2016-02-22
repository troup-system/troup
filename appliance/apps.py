__author__ = 'pavle'


class App:

    def __init__(self, name, description, command, tunnel_audio=False, tunnel_video=False):
        self.name = name
        self.description = description
        self.command = command
        self.tunnel_audio = tunnel_audio
        self.tunnel_video = tunnel_video

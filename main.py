import pygame as pg
import pygame.midi

class Keyboard:
    def __init__(self):
        if not pg.get_init():
            pg.init()
        if not pg.midi.get_init():
            pg.midi.init()
        if not pg.mixer.get_init():
            pg.mixer.init()
        self.input_id = pg.midi.get_default_input_id()
        self.output_id = pg.midi.get_default_output_id()
        try:
            self.akai = pg.midi.Input(self.input_id)
        except pg.midi.MidiException:
            print("the following input device could not connect: ", pg.midi.get_device_info(self.input_id))
            raise
        try:
            self.player = pg.midi.Output(self.output_id)
        except pg.midi.MidiException:
            print("the following input device could not connect: ", pg.midi.get_device_info(self.output_id))
            raise
        self.instrument = 0
        self.drum_map = {48: 35, 49: 36, 50: 38, 51: 39, 44: 42, 45: 44, 46: 51, 47: 59}
        self.recorded_events = []
        self.is_recording = False
        self.is_looping = False
        self.start_recording = 0
        self.stop_recording = 0
        self.drums_enabled = True

    # returns a list of instrument options
    @staticmethod
    def instruments():
        print(
            "0-7: Piano\n8-15 Chromatic Percussion\n16-23 Organ\n24-31 Guitar\n32-39 Bass\n40-47 Strings\n48-55 "
            "Ensemble\n56-63 Brass\n64-71 Reed\n72-79 Pipe\n80-87 Synth Lead\n88-95 Synth Pad\n96-103 Synth "
            "Effects\n104-111 Ethnic\n112-119 Percussive\n120-127 Sound Effects")

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.start_recording = pg.time.get_ticks()
        else:
            self.is_recording = False
            self.stop_recording = pg.time.get_ticks()
            self.is_looping = True

    def play_recorded_loop(self):
        assert not self.is_recording
        assert self.is_looping
        # if dt < self.recorded_events:

        if len(self.recorded_events) < 1:
            self.is_looping = False
            return

        recording_start_time = self.start_recording
        recorded_time_of_next_note = self.recorded_events[0].timestamp
        looping_start_time = self.stop_recording
        duration = self.stop_recording - self.start_recording

        time_since_loop_start = pg.time.get_ticks() - looping_start_time
        note_time_since_recording_start = recorded_time_of_next_note - recording_start_time

        if time_since_loop_start < note_time_since_recording_start:
            return

        if note_time_since_recording_start >= duration:
            self.is_looping = False
            return

        event = self.recorded_events.pop(0)
        self.handle_event(event)

    @property
    def instrument(self):
        return self.__instrument

    @instrument.setter
    def instrument(self, number):
        self.__instrument = number
        self.player.set_instrument(number)

    def handle_event(self, event):
        note_on = 144
        note_off = 128
        channel = 0
        note = event.note
        # modifies sound for drum pads
        if self.drums_enabled and 44 <= event.note <= 51:
            note = self.drum_map[event.note]
            channel = 9
        # plays the note
        if event.status == note_on:
            self.player.note_on(note, event.velocity, channel)
        elif event.status == note_off:
            self.player.note_off(note, event.velocity, channel)

    # post events from the keyboard to the event loop
    def get_akai_events(self):
        if self.akai.poll():
            midi_events = self.akai.read(1)
            status = midi_events[0][0][0]
            note = midi_events[0][0][1]
            velocity = midi_events[0][0][2]
            timestamp = midi_events[0][1]
            ev = pg.event.Event(pg.USEREVENT,
                                {'status': status, 'note': note, 'velocity': velocity, 'timestamp': timestamp})
            pg.event.post(ev)

    def game_loop(self):
        is_running = True
        dt = 0
        clock = pg.time.Clock()
        screen = pg.display.set_mode((500, 500))

        while is_running:
            events = pg.event.get()
            for e in events:
                print(e)
                if e.type == pg.QUIT:
                    is_running = False
                elif e.type == pg.USEREVENT:
                    self.handle_event(e)
                    if self.is_recording:
                        self.recorded_events.append(e)
                elif e.type == pg.KEYDOWN:
                    self.handle_keys(e)

            # updates
            screen.fill((30, 30, 30))
            pg.display.update()
            self.get_akai_events()
            if self.is_looping:
                self.play_recorded_loop()
            dt = clock.tick(120)

    def toggle_drums(self):
        if self.drums_enabled:
            self.drums_enabled = False
        else:
            self.drums_enabled = True

    def handle_keys(self, e):
        space_bar = 32
        q = 113
        if e.key == space_bar:
            self.toggle_recording()
        elif e.key == q:
            self.toggle_drums()

    # closes midi streams and unloads pygame modules
    def __del__(self):
        self.akai.close()
        self.player.close()
        pg.midi.quit()
        pg.mixer.quit()
        pg.quit()


def main():
    print("ok lets get this working")
    keyboard = Keyboard()
    keyboard.game_loop()


if __name__ == '__main__':
    main()

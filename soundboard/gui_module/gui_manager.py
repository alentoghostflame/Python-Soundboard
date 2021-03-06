from soundboard.audio_module import AudioManager
from typing import List, Optional
import tkinter as tk
import logging
from soundboard.storage_module import StorageManager, SoundboardConfig
from soundboard.input_module import InputManager


logger = logging.getLogger("soundboard")


class SoundboardWindow:
    def __init__(self, config: SoundboardConfig, storage: StorageManager, audio: AudioManager, input_man: InputManager):
        self._config: SoundboardConfig = config
        self._storage: StorageManager = storage
        self._data: SoundboardData = SoundboardData(storage)
        self._audio: AudioManager = audio
        self._input: InputManager = input_man
        self._window = tk.Tk()

        self.file_list = FileListFrame(self._window, self._storage, self._audio, self._data)
        self.folder_list = FolderListFrame(self._window, self._storage, self._data, self.file_list)
        self.audio_buttons = AudioButtonsFrame(self._window, self._storage, self._audio, self._data, self.folder_list)
        self.top_bar = TopBarFrame(self._window, self._config, self._storage, self._input, self._data, self._audio,
                                   self.folder_list, self.file_list)

    def _setup_children(self):
        self.top_bar.grid(column=0, row=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        self.folder_list.grid(column=0, row=1, padx=5, pady=5, sticky=tk.NSEW)
        self.audio_buttons.grid(column=1, row=1, padx=5, pady=5, sticky=tk.NSEW)
        self.file_list.grid(column=2, row=1, padx=5, pady=5, sticky=tk.NSEW)

    def setup(self):
        logger.debug("Running Soundboard setup.")
        self._window.title("Python Linux Soundboard")
        self._window.columnconfigure(0, weight=1)
        self._window.columnconfigure(2, weight=1)
        self._window.rowconfigure(1, weight=1)
        self._setup_children()

        mapped_folders = self._storage.get_mapped_folders()
        if mapped_folders:
            self._data.selected_folder = 0

    def run(self):
        logger.debug("Starting the GUI mainloop.")
        self.top_bar.buttons.refresh_files()
        self._window.mainloop()

    def press_audio_button(self, index: int):
        self.audio_buttons.press_audio_button(index)

    def increment_page(self):
        self.audio_buttons.increment_page()

    def decrement_page(self):
        self.audio_buttons.decrement_page()


class SoundboardData:
    def __init__(self, storage: StorageManager):
        self._storage = storage
        self._selected_folder: Optional[int] = None

    def reset_selected(self):
        if self._storage.get_mapped_folders():
            self._selected_folder = 0
        else:
            self._selected_folder = None

    def get_selected(self) -> int:
        mapped_folders = self._storage.get_mapped_folders()
        if self._selected_folder >= len(mapped_folders):
            self._selected_folder = len(mapped_folders) - 1
        elif self._selected_folder < 0:
            self._selected_folder = 0
        return self._selected_folder

    def increment_selected(self):
        self._selected_folder += 1
        if self._selected_folder >= len(self._storage.get_mapped_folders()):
            self._selected_folder = 0

    def decrement_selected(self):
        self._selected_folder -= 1
        if self._selected_folder < 0:
            self._selected_folder = len(self._storage.get_mapped_folders()) - 1

    def set_selected(self, index: int):
        self._selected_folder = index


class FileListFrame(tk.LabelFrame):
    def __init__(self, window: tk.Tk, storage: StorageManager, audio: AudioManager, data: SoundboardData):
        tk.LabelFrame.__init__(self, window, text="Files", padx=5, pady=5)
        self._storage = storage
        self._audio = audio
        self._data = data
        self.listbox = tk.Listbox(self, width=15)
        self.scroll_vert = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scroll_hori = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self._run_setup()

    def _run_setup(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.listbox.grid(column=0, row=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.listbox.bind("<ButtonRelease-1>", self.on_select)

        self.scroll_vert.config(command=self.listbox.yview)
        self.scroll_vert.grid(column=1, row=0, sticky=tk.NS + tk.E)
        self.listbox.config(yscrollcommand=self.scroll_vert.set)

        self.scroll_hori.config(command=self.listbox.xview)
        self.scroll_hori.grid(column=0, row=1, sticky=tk.S + tk.EW)
        self.listbox.config(xscrollcommand=self.scroll_hori.set)

    def on_select(self, dummy):
        if len(self.listbox.curselection()) > 0:
            index = self.listbox.curselection()[0]
            # sound_path = self._storage.get_indexed_sound(self._data.get_selected(), index)
            sound_path = \
                self._storage.get_discovered()[self._storage.get_mapped_folders()[self._data.get_selected()]][index]
            self._audio.play_sound(sound_path)

    def update_display(self):
        # mapped_folders = self._storage.get_mapped_folders()
        # mapped_sounds = self._storage.get_mapped_sounds()
        # self.listbox.delete(0, tk.END)
        # for index in mapped_sounds[mapped_folders[self._data.get_selected()]]:
        #     self.listbox.insert(tk.END, mapped_sounds[mapped_folders[self._data.get_selected()]][index].name)
        self.listbox.delete(0, tk.END)
        discovered_sounds = self._storage.get_discovered()
        for sound_path in discovered_sounds[self._storage.get_mapped_folders()[self._data.get_selected()]]:
            self.listbox.insert(tk.END, sound_path.name)


class FolderListFrame(tk.LabelFrame):
    def __init__(self, window: tk.Tk, storage: StorageManager, data: SoundboardData, file_list: FileListFrame):
        tk.LabelFrame.__init__(self, window, text="Folders", padx=5, pady=5)
        self._storage = storage
        self._data = data
        self._file_list = file_list
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(self, width=15)
        self.scroll_vert = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scroll_hori = tk.Scrollbar(self, orient=tk.HORIZONTAL)

        self._run_setup()

    def _run_setup(self):
        self.listbox.grid(column=0, row=0, sticky=tk.NSEW)
        self.listbox.bind("<ButtonRelease-1>", self.on_select)
        self.listbox.config(selectmode=tk.SINGLE)
        self.scroll_vert.config(command=self.listbox.yview)
        self.scroll_vert.grid(column=1, row=0, sticky=tk.NS + tk.E)
        self.listbox.config(yscrollcommand=self.scroll_vert.set)
        self.scroll_hori.config(command=self.listbox.xview)
        self.scroll_hori.grid(column=0, row=1, sticky=tk.S + tk.E + tk.W)
        self.listbox.config(xscrollcommand=self.scroll_hori.set)

    def set_selected(self, index: int):
        if index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.select_set(index)
            self.on_select()

    def on_select(self, dummy=None):
        if len(self.listbox.curselection()) > 0:
            self._data.set_selected(self.listbox.curselection()[0])
            self._file_list.update_display()

    def update_display(self):
        mapped_folders = self._storage.get_mapped_folders()
        self.listbox.delete(0, tk.END)
        for folder in mapped_folders:
            self.listbox.insert(tk.END, folder.name)


class AudioButtonsFrame(tk.LabelFrame):
    def __init__(self, window: tk.Tk, storage: StorageManager, audio: AudioManager, data: SoundboardData,
                 folder_list: FolderListFrame):
        tk.LabelFrame.__init__(self, window, text="Play Buttons", padx=5, pady=5)
        self._data = data
        self._folder_list = folder_list
        self.forward_page = tk.Button(self, text=" + Folder", width=7, command=self.increment_page)
        self.back_page = tk.Button(self, text=" - Folder", width=7, command=self.decrement_page)
        self.clear_audio = tk.Button(self, text="0 Stop", width=7, command=audio.stop_sounds)
        self.audio_buttons: List[AudioButton] = list()

        for i in range(9):
            self.audio_buttons.append(AudioButton(self, storage, audio, data, i))
        self._run_setup()

    def _run_setup(self):
        self.forward_page.grid(column=2, row=0, padx=5, pady=5)
        self.back_page.grid(column=0, row=0, padx=5, pady=5)
        self.clear_audio.grid(column=0, row=4)
        self._place_audio_buttons()

    def _place_audio_buttons(self):
        for button in self.audio_buttons:
            button.grid(column=button.get_index() % 3, row=3 - button.get_index() // 3)

    def increment_page(self):
        self._data.increment_selected()
        self._folder_list.set_selected(self._data.get_selected())

    def decrement_page(self):
        self._data.decrement_selected()
        self._folder_list.set_selected(self._data.get_selected())

    def press_audio_button(self, index: int):
        if index < len(self.audio_buttons):
            self.audio_buttons[index].play_sound()


class AudioButton(tk.Button):
    def __init__(self, label_frame: tk.LabelFrame, storage: StorageManager, audio: AudioManager, data: SoundboardData,
                 index: int):
        tk.Button.__init__(self, label_frame, text=f"{index + 1} Play", width=7, command=self.play_sound)
        self._storage = storage
        self._audio = audio
        self._data = data
        self._index: int = index

    def get_index(self) -> int:
        return self._index

    def play_sound(self):
        selected_folder_index = self._data.get_selected()
        mapped_folders = self._storage.get_mapped_folders()
        sound_path = self._storage.get_mapped_sound(mapped_folders[selected_folder_index], self._index)
        if sound_path:
            logger.debug(f"Playing sound {sound_path.name}")
            self._audio.play_sound(sound_path)
        else:
            logger.debug(f"User tried to play sound {self._index + 1}, but no sound was mapped to that.")


class TopBarFrame(tk.Frame):
    def __init__(self, window: tk.Tk, config: SoundboardConfig, storage: StorageManager, input_man: InputManager,
                 data: SoundboardData, audio: AudioManager, folder_list: FolderListFrame, file_list: FileListFrame):
        tk.Frame.__init__(self, window)
        self._config = config
        self.audio = audio
        self.buttons = TopBarButtonFrame(self, storage, input_man, data, folder_list, file_list)
        self.buttons.grid(column=0, row=0, sticky=tk.NW)
        self.audio_count = tk.Label(self, text="Audio Thread Count: [PH] / [PH]")

        self._setup_layout()

    def _setup_layout(self):
        self.columnconfigure(0, weight=1)
        self.audio_count.grid(column=3, row=0, padx=5, pady=5, sticky=tk.E)
        self.update_audio_count()

    def update_audio_count(self):
        self.audio_count.config(text=f"Audio Thread Count: {self.audio.get_audio_count()} / {self._config.max_sounds}")
        self.after(50, self.update_audio_count)


class TopBarButtonFrame(tk.Frame):
    def __init__(self, frame: tk.Frame, storage: StorageManager, input_man: InputManager, data: SoundboardData,
                 folder_list: FolderListFrame, file_list: FileListFrame):
        tk.Frame.__init__(self, frame)
        self._storage = storage
        self._input = input_man
        self._data = data
        self._folder_list = folder_list
        self._file_list = file_list
        self._selection_var = tk.StringVar()

        self.refresh_button = tk.Button(self, text="Refresh", command=self.refresh_files)
        self.event_file_button = tk.Button(self, text="Use Event File", command=self.on_event_button)
        self.event_file_pulldown = tk.OptionMenu(self, self._selection_var, "None")

        self._setup_layout()

    def _setup_layout(self):
        self.refresh_button.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.event_file_button.grid(column=1, row=0, padx=5, pady=5, sticky=tk.W)
        self.event_file_pulldown.grid(column=2, row=0, padx=5, pady=5, sticky=tk.W)
        self._selection_var.set("None")

    def update_event_pulldown(self):
        self.event_file_pulldown.selection_clear()
        self.event_file_pulldown["menu"].delete(0, tk.END)
        self.event_file_pulldown["menu"].add_command(label="None", command=tk._setit(self._selection_var, "None"))
        for event_path in self._storage.get_input_files():
            self.event_file_pulldown["menu"].add_command(label=event_path.name,
                                                         command=tk._setit(self._selection_var, event_path.name))
        self._selection_var.set("None")

    def on_event_button(self, dummy=None):
        logger.debug(f"{dummy}, {self._selection_var.get()}")
        path = self._storage.str_to_input(self._selection_var.get())
        if path is None:
            logger.warning(f"Somehow, a path wasn't found for {self._selection_var.get()}")
        else:
            self._input.set_event_path(path)

    def refresh_files(self):
        logger.debug("User asked to refresh files.")
        self._storage.reset_sounds()
        self._storage.discover()
        self._storage.map()
        self._data.reset_selected()
        self._folder_list.update_display()
        self._file_list.update_display()
        self.update_event_pulldown()


# How to run:
# 1. Add the auto_lip_sync folder to your Maya scripts folder (username\Documents\maya\*version*\scripts).
# 2. Insert your conda.exe path to the code (usually found in: C:\Users\username\miniconda3\Scripts\conda.exe). Be sure of the dependencies for each virtual ambient.
# 3. To start the auto lipsync tool in Maya, execute the following lines of code in the Script editor:
#    import auto_lip_sync
#    auto_lip_sync.start()

import shutil
import os
import sys
import json
import subprocess
import webbrowser
import traceback
import re

from maya import OpenMaya, OpenMayaUI, mel, cmds
from shiboken2 import wrapInstance
from collections import OrderedDict
from PySide2 import QtCore, QtGui, QtWidgets

# Insert your full conda path
conda_exe = 'C:/Users/ferni/miniconda3/Scripts/conda.exe'

# Import Textgrid module (kylebgorman/textgrid).
try:
    import textgrid
except ImportError:
    print("error in importing textgrid module")


class PoseConnectWidget(QtWidgets.QWidget):
    def __init__(self, label, parent=None):
        super(PoseConnectWidget, self).__init__(parent)
        self.combo_label = label
        self.create_ui_widgets()
        self.create_ui_layout()

    def create_ui_widgets(self):
        self.save_pose_combo = QtWidgets.QComboBox()
        self.pose_key_label = QtWidgets.QLabel(self.combo_label)
        self.pose_key_label.setFixedWidth(40)
        self.pose_key_label.setStyleSheet("border: 1px solid #303030;")

    def create_ui_layout(self):
        combo_row = QtWidgets.QHBoxLayout(self)
        combo_row.addWidget(self.pose_key_label)
        combo_row.addWidget(self.save_pose_combo)
        combo_row.setContentsMargins(0, 0, 0, 0)

    def set_text(self, value):
        self.save_pose_combo.addItems(value)

    def get_text(self):
        return self.save_pose_combo.currentText()

    def clear_box(self):
        self.save_pose_combo.clear()


class LipSyncDialog(QtWidgets.QDialog):

    WINDOW_TITLE = "Auto lip sync"
    PYTHON_VERSION = float(re.search(r'\d+\.\d+', sys.version).group())

    USER_SCRIPT_DIR = cmds.internalVar(userScriptDir=True)
    OUTPUT_FOLDER_PATH = USER_SCRIPT_DIR+"output"
    INPUT_FOLDER_PATH = USER_SCRIPT_DIR+"input"

    MFA_PATH = USER_SCRIPT_DIR+"montreal-forced-aligner/bin"
    if os.path.exists(MFA_PATH) == False:
        cmds.confirmDialog(title="Path doesn't exist!",
                           message="This path doesn't exist: "+MFA_PATH)

    SER_SCRIPT_PATH = USER_SCRIPT_DIR+"emotion-classifier/predict_script.py"
    SER_MODEL_PATH = USER_SCRIPT_DIR+"emotion-classifier/SER_model1.h5"
    SER_PATH = USER_SCRIPT_DIR + 'temp/'

    sound_clip_path = ""
    text_file_path = ""
    pose_folder_path = ""
    active_controls = []

    phone_dict = {}
    phone_path_dict = OrderedDict([
        ("neutral", ""),
        ("happy", ""),
        ("sad", ""),
        ("AA", ""),
        ("EE", ""),
        ("U", ""),
        ("Er", ""),
        ("O", ""),
        ("KSTN", ""),
        ("TSCH", ""),
        ("FV", ""),
        ("WQ", ""),
        ("BMP", ""),
        ("rest", "")
    ])

    def __init__(self):

        main_window = OpenMayaUI.MQtUtil.mainWindow()
        if sys.version_info.major < 3:
            maya_main_window = wrapInstance(
                long(main_window), QtWidgets.QWidget)  # type: ignore
        else:
            maya_main_window = wrapInstance(
                int(main_window), QtWidgets.QWidget)

        super(LipSyncDialog, self).__init__(maya_main_window)

        self.widget_list = []
        self.counter = 0
        self.maya_color_list = [13, 18, 14, 17]
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(380, 100)
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()

        # Set default language paths
        self.update_language_paths()

    def create_ui_widgets(self):
        self.sound_text_label = QtWidgets.QLabel("Input wav.file:")
        self.sound_filepath_line = QtWidgets.QLineEdit()
        self.sound_filepath_button = QtWidgets.QPushButton()
        self.sound_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.sound_filepath_line.setText(self.sound_clip_path)

        self.text_input_label = QtWidgets.QLabel("Input txt.file:")
        self.text_filepath_line = QtWidgets.QLineEdit()
        self.text_filepath_button = QtWidgets.QPushButton()
        self.text_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.text_filepath_line.setText(self.text_file_path)

        self.language_label = QtWidgets.QLabel("Select language:")
        self.language_combo_box = QtWidgets.QComboBox()
        self.language_combo_box.addItems(["English", "Japanese"])
        self.language_combo_box.currentIndexChanged.connect(
            self.update_language_paths)

        self.pose_folder_label = QtWidgets.QLabel("Pose folder:")
        self.pose_filepath_line = QtWidgets.QLineEdit()
        self.pose_filepath_button = QtWidgets.QPushButton()
        self.pose_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.pose_refresh_button = QtWidgets.QPushButton()
        self.pose_refresh_button.setIcon(QtGui.QIcon(":refresh.png"))
        self.pose_filepath_line.setText(self.pose_folder_path)

        self.generate_keys_button = QtWidgets.QPushButton("Generate keyframes")
        self.generate_keys_button.setStyleSheet(
            "background-color: lightgreen; color: black")
        self.save_pose_button = QtWidgets.QPushButton("Save pose")
        self.load_pose_button = QtWidgets.QPushButton("Load pose")
        self.close_button = QtWidgets.QPushButton("Close")

        self.separator_line = QtWidgets.QFrame(parent=None)
        self.separator_line.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator_line.setFrameShadow(QtWidgets.QFrame.Sunken)

    def create_ui_layout(self):
        sound_input_row = QtWidgets.QHBoxLayout()
        sound_input_row.addWidget(self.sound_text_label)
        sound_input_row.addWidget(self.sound_filepath_line)
        sound_input_row.addWidget(self.sound_filepath_button)

        text_input_row = QtWidgets.QHBoxLayout()
        text_input_row.addWidget(self.text_input_label)
        text_input_row.addWidget(self.text_filepath_line)
        text_input_row.addWidget(self.text_filepath_button)

        language_selection_row = QtWidgets.QHBoxLayout()
        language_selection_row.addWidget(self.language_label)
        language_selection_row.addWidget(self.language_combo_box)

        pose_input_row = QtWidgets.QHBoxLayout()
        pose_input_row.addWidget(self.pose_folder_label)
        pose_input_row.addWidget(self.pose_filepath_line)
        pose_input_row.addWidget(self.pose_filepath_button)
        pose_input_row.addWidget(self.pose_refresh_button)

        pose_buttons_row = QtWidgets.QHBoxLayout()
        pose_buttons_row.addWidget(self.load_pose_button)
        pose_buttons_row.addWidget(self.save_pose_button)

        bottom_buttons_row = QtWidgets.QHBoxLayout()
        bottom_buttons_row.addWidget(self.generate_keys_button)
        bottom_buttons_row.addWidget(self.close_button)

        pose_widget_layout = QtWidgets.QVBoxLayout()
        for key in list(self.phone_path_dict.keys()):
            pose_connect_widget = PoseConnectWidget(key)
            pose_widget_layout.addWidget(pose_connect_widget)
            pose_connect_widget.set_text(self.get_pose_paths())
            self.widget_list.append(pose_connect_widget)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addLayout(sound_input_row)
        main_layout.addLayout(text_input_row)
        main_layout.addLayout(language_selection_row)
        main_layout.addWidget(self.separator_line)
        main_layout.addLayout(pose_input_row)
        main_layout.addLayout(pose_buttons_row)
        main_layout.addLayout(pose_widget_layout)
        main_layout.addLayout(bottom_buttons_row)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

    def create_ui_connections(self):
        self.sound_filepath_button.clicked.connect(self.input_sound_dialog)
        self.text_filepath_button.clicked.connect(self.input_text_dialog)
        self.pose_filepath_button.clicked.connect(self.pose_folder_dialog)
        self.save_pose_button.clicked.connect(self.save_pose_dialog)
        self.load_pose_button.clicked.connect(self.load_pose_dialog)
        self.pose_refresh_button.clicked.connect(self.refresh_pose_widgets)
        self.close_button.clicked.connect(self.close_window)
        self.generate_keys_button.clicked.connect(self.generate_animation)

    def pose_folder_dialog(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select pose folder path", "")
        if folder_path:
            self.pose_filepath_line.setText(folder_path)
            self.pose_folder_path = folder_path
            self.refresh_pose_widgets()

    def input_sound_dialog(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select sound clip", "", "Wav (*.wav);;All files (*.*)")
        if file_path[0]:
            self.sound_filepath_line.setText(file_path[0])
            self.sound_clip_path = file_path[0]

    def save_pose_dialog(self):
        file_path = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save pose file", self.pose_folder_path, "Pose file (*.json);;All files (*.*)")
        if file_path[0]:
            self.save_pose(file_path[0])
            print("Saved pose: "+file_path[0])

    def load_pose_dialog(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Save pose file", self.pose_folder_path, "Pose file (*.json);;All files (*.*)")
        if file_path[0]:
            self.load_pose(file_path[0])
            print("Loaded pose: "+file_path[0])

    def input_text_dialog(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select dialog transcript", "", "Text (*.txt);;All files (*.*)")
        if file_path[0]:
            self.text_filepath_line.setText(file_path[0])
            self.text_file_path = file_path[0]

    def find_textgrid_file(self):
        path = self.OUTPUT_FOLDER_PATH
        textgrid_file = ""
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".TextGrid"):
                    textgrid_file = root+"/"+file
        return textgrid_file

    def find_txt_file(self):
        path = self.OUTPUT_FOLDER_PATH
        txt_file = ""
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".txt"):
                    txt_file = root+"/"+file
        return txt_file

    def update_language_paths(self):
        selected_language = self.language_combo_box.currentText()
        if selected_language == "English":
            self.LANGUAGE_PATH = self.USER_SCRIPT_DIR + \
                "montreal-forced-aligner/pretrained_models/english_us_arpa.zip"
            print("LANGUAGE_PATH: ", self.LANGUAGE_PATH)
            self.LEXICON_PATH = self.USER_SCRIPT_DIR + "librispeech-lexicon.txt"
            self.phone_dict = {
                "AA0": "AA", "AA1": "AA", "AA2": "AA", "AE0": "AA", "AE1": "AA", "AE2": "AA",
                "AH0": "AA", "AH1": "AA", "AH2": "AA", "AO0": "AA", "AO1": "AA", "AO2": "AA",
                "AW0": "WQ", "AW1": "WQ", "AW2": "WQ", "AY0": "AA", "AY1": "AA", "AY2": "AA",
                "EH0": "EE", "EH1": "EE", "EH2": "EE", "ER0": "O", "ER1": "O", "ER2": "O", "EY0": "EE",
                "EY1": "EE", "EY2": "E", "IH0": "AA", "IH1": "AA", "IH2": "AA", "IY0": "EE", "IY1": "EE",
                "IY2": "EE", "OW0": "O", "OW1": "O", "OW2": "O", "OY0": "O", "OY1": "O", "OY2": "O",
                "UH0": "U", "UH1": "U", "UH2": "U", "UW0": "U", "UW1": "U", "UW2": "U", "B": "BMP",
                "CH": "TSCH", "D": "KSTN", "DH": "KSTN", "F": "FV", "G": "KSTN", "HH": "EE", "JH": "EE",
                "K": "KSTN", "L": "L", "M": "BMP", "N": "KSTN", "NG": "KSTN", "P": "BMP", "R": "KSTN",
                "S": "KSTN", "SH": "TSCH", "T": "TSCH", "TH": "KSTN", "V": "FV", "W": "WQ", "Y": "EE",
                "Z": "EE", "ZH": "KSTN", "sil": "rest", "None": "rest", "sp": "rest", "spn": "rest", "": "rest"
            }
        elif selected_language == "Japanese":
            self.LANGUAGE_PATH = self.USER_SCRIPT_DIR + \
                "montreal-forced-aligner/pretrained_models/jp_model2.zip"
            self.LEXICON_PATH = self.USER_SCRIPT_DIR + "jp_dict_simple.txt"
            self.phone_dict = {
                "a": "AA", "i": "EE", "u": "U", "e": "Er", "o": "O",
                "k": "KSTN", "g": "KSTN", "s": "KSTN", "t": "KSTN", "d": "KSTN", "n": "KSTN", "z": "KSTN",
                "sh": "TSCH", "ch": "TSCH", "ts": "TSCH", "j": "TSCH", "ji": "TSCH", "f": "FV", "v": "FV",
                "m": "BMP", "b": "BMP", "p": "BMP", "w": "WQ", "nn": "BMP",
                "ni": "EE", "nu": "U", "ha": "AA", "hi": "EE", "he": "E", "ho": "O",
                "ra": "AA", "ri": "EE", "ru": "U", "re": "Er", "ro": "O",
                "an": "AA", "in": "EE", "un": "U", "en": "Er", "on": "O",
                "nin": "EE", "nun": "U", "han": "A", "hin": "EE", "hen": "Er", "hon": "O",
                "ran": "AA", "rin": "EE", "run": "U", "ren": "Er", "ron": "O",
                "sil": "rest", "None": "rest", "sp": "rest", "spn": "rest", "": "rest"
            }

        if not os.path.exists(self.LANGUAGE_PATH):
            cmds.confirmDialog(title="Path doesn't exist!",
                               message="This path doesn't exist: " + self.LANGUAGE_PATH)

        if not os.path.exists(self.LEXICON_PATH):
            cmds.confirmDialog(title="Path doesn't exist!",
                               message="This path doesn't exist: " + self.LEXICON_PATH)

    def open_readme(self):
        pass

    def generate_animation(self):
        number_of_operations = 12
        current_operation = 0
        p_dialog = QtWidgets.QProgressDialog(
            "Analyzing the input data and generating keyframes...", "Cancel", 0, number_of_operations, self)
        p_dialog.setWindowFlags(p_dialog.windowFlags()
                                ^ QtCore.Qt.WindowCloseButtonHint)
        p_dialog.setWindowTitle("Progress...")
        p_dialog.setValue(0)
        p_dialog.setWindowModality(QtCore.Qt.WindowModal)
        p_dialog.show()
        QtCore.QCoreApplication.processEvents()

        self.create_clean_input_folder()
        self.update_phone_paths()
        p_dialog.setValue(current_operation + 1)

        try:
            self.import_sound()
        except:
            traceback.print_exc()
            cmds.warning("Could not import sound file.")
        p_dialog.setValue(current_operation + 1)

        # Speech Emotion Recognition ambient
        conda_environment = 'ser'

        print("SER_PATH: ", self.SER_PATH)
        print("sound_clip_path", self.sound_clip_path)
        command = [
            conda_exe, 'run', '-n', conda_environment, 'python', self.SER_SCRIPT_PATH,
            '--model', self.SER_MODEL_PATH,
            '--audio', self.sound_clip_path,
            '--output', self.SER_PATH
        ]
        print("Comando:", command)
        subprocess.run(command)
        print("SER subprocess OK.")

        # MFA ambient
        conda_environment = 'aligner'

        command = (
            conda_exe + " run -n " + conda_environment + " mfa align " +
            self.INPUT_FOLDER_PATH + " " + self.LEXICON_PATH + " " +
            self.LANGUAGE_PATH + " " + self.OUTPUT_FOLDER_PATH
        )
        print("Comando:", command)

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        def decode_line(line):
            try:
                return line.decode('utf-8')
            except UnicodeDecodeError:
                return line.decode('utf-8', errors='ignore')

        print("stdout:")
        for line in process.stdout:
            if line.strip():
                print("STDOUT:", decode_line(line))

        print("stderr:")
        for line in process.stderr:
            if line.strip():
                print("STDERR:", decode_line(line))

        process.wait()

        try:
            self.create_keyframes()
            print("Successfully generated keyframes.")
            p_dialog.setValue(number_of_operations)
            p_dialog.close()
        except:
            traceback.print_exc()
            p_dialog.setValue(number_of_operations)
            p_dialog.close()

        self.delete_input_folder()

    def get_emotion_shape(self):
        try:
            with open(self.SER_PATH+"class.txt", 'r') as file:
                emotion_shape = file.read().strip()
                print(
                    f'class.txt content: {emotion_shape}')
        except FileNotFoundError:
            print('class.txt not found.')
        except Exception as e:
            print(
                f'Error when tried to read class.txt: {e}')
        return emotion_shape

    def import_sound(self):
        cmds.sound(file=self.sound_clip_path, name="SoundFile")
        gPlayBackSlider = mel.eval("$tmpVar=$gPlayBackSlider")
        cmds.timeControl(gPlayBackSlider, edit=True, sound="SoundFile")

    def delete_input_folder(self):
        try:
            shutil.rmtree(self.INPUT_FOLDER_PATH)
            shutil.rmtree(self.OUTPUT_FOLDER_PATH)
        except:
            pass

    def create_clean_input_folder(self):

        self.delete_input_folder()

        # Create temp folder
        os.mkdir(self.INPUT_FOLDER_PATH)
        sound_source = self.sound_clip_path
        text_source = self.text_file_path
        destination = self.INPUT_FOLDER_PATH

        # Copy files
        shutil.copy(sound_source, destination)
        shutil.copy(text_source, destination)

        # Rename text file so it matches sound file (Shutil copy doesn't return path in Python2)
        sound_name = ""
        for file in os.listdir(destination):
            if file.endswith(".wav"):
                sound_name = file.split(".")[0]

        for file in os.listdir(destination):
            if file.endswith(".txt"):
                old_name = self.INPUT_FOLDER_PATH+"/"+file
                new_name = self.INPUT_FOLDER_PATH+"/"+sound_name+".txt"
                os.rename(old_name, new_name)

    def create_keyframes(self):
        textgrid_path = self.find_textgrid_file()
        tg = textgrid.TextGrid.fromFile(textgrid_path)
        iterations = len(tg[1])
        print(tg[1])

        emotion_pos = self.get_emotion_shape()
        print("Predicted emotion: ", emotion_pos)
        try:
            for k in self.phone_path_dict:
                if emotion_pos in k:
                    pose_path = self.phone_path_dict.get(k)
                    print("pose_path: {}\n".format(pose_path))
            self.load_pose(pose_path)
            print(self.load_pose(pose_path))

            print("emotion: {}, min_time: {}\n".format(emotion_pos, min_time))
            try:
                cmds.setKeyframe(self.active_controls, time=[
                    "0.00"+"sec", "0.01"+"sec"])
            except:
                print("Failed to set keyframe")

            try:
                cmds.keyTangent(self.active_controls,
                                inTangentType="spline", outTangentType="spline")
            except:
                print("Failed to set keytangent")
        except:
            print("failed to keyframe emotion")

        for i in range(iterations):
            min_time = str(tg[1][i].minTime)
            max_time = str(tg[1][i].maxTime)
            phone = tg[1][i].mark
            # print(phone, min_time)

            # Get the phone pose paths from the dict and load the correlated pose
            key_value = self.phone_dict.get(phone)

            print("key_value: {}, min_time: {}\n".format(key_value, min_time))
            for k in self.phone_path_dict:
                if key_value in k:
                    pose_path = self.phone_path_dict.get(k)
                    print("pose_path: {}\n".format(pose_path))

            self.load_pose(pose_path)
            print(self.load_pose(pose_path))

            try:
                cmds.setKeyframe(self.active_controls, time=[
                                 min_time+"sec", max_time+"sec"])
            except:
                print("Failed to set keyframe")

            try:
                cmds.keyTangent(self.active_controls,
                                inTangentType="spline", outTangentType="spline")
            except:
                print("Failed to set keytangent")

    def save_pose(self, pose_path):
        controllers = cmds.ls(sl=True)
        controller_dict = OrderedDict()
        attr_dict = OrderedDict()

        for ctrl in controllers:
            keyable_attr_list = cmds.listAttr(
                ctrl, keyable=True, unlocked=True)

            for attr in keyable_attr_list:
                attr_value = cmds.getAttr(ctrl+"."+attr)
                attr_dict[attr] = attr_value

            controller_dict[ctrl] = attr_dict
            attr_dict = {}
        save_path = pose_path

        with open(save_path, "w") as jsonFile:
            json.dump(controller_dict, jsonFile, indent=4)

    def load_pose(self, file_path):
        pose_data = json.load(open(file_path))
        self.active_controls = []

        if self.PYTHON_VERSION < 3:
            for ctrl, input in pose_data.iteritems():
                for attr, value in input.iteritems():
                    cmds.setAttr(ctrl+"."+attr, value)
                self.active_controls.append(ctrl)
        else:
            for ctrl, input in pose_data.items():
                for attr, value in input.items():
                    cmds.setAttr(ctrl+"."+attr, value)
                self.active_controls.append(ctrl)

    def get_pose_paths(self):
        pose_list = []
        folder_path = self.pose_folder_path
        try:
            for file in os.listdir(folder_path):
                if file.endswith(".json"):
                    pose_list.append(folder_path+"/"+file)
            return pose_list
        except:
            return pose_list

    def refresh_pose_widgets(self):
        print(self.phone_dict)
        for w in self.widget_list:
            w.clear_box()
            w.set_text(self.get_pose_paths())

    def update_phone_paths(self):
        for index, key in enumerate(self.phone_path_dict):
            self.phone_path_dict[key] = self.widget_list[index].get_text()

    def close_window(self):
        self.close()
        self.deleteLater()


def start():
    global lip_sync_ui
    try:
        lip_sync_ui.close()  # type: ignore
        lip_sync_ui.deleteLater()  # type: ignore
    except:
        pass
    lip_sync_ui = LipSyncDialog()
    lip_sync_ui.show()


if __name__ == "__main__":
    start()

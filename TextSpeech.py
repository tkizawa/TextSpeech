import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import azure.cognitiveservices.speech as speechsdk

class TextToSpeechApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Text to Speech")

        # 音声選択用の変数を初期化
        self.voice_var = tk.StringVar()
        self.voice_var.set("ja-JP-NanamiNeural")  # デフォルト値を設定

        # ウィンドウ設定を読み込む（この時点で voice_var が使用可能）
        self.master.geometry(self.load_window_settings())

        self.text_input = tk.Text(self.master, wrap=tk.WORD)
        self.text_input.pack(expand=True, fill='both', padx=10, pady=10)

        control_frame = tk.Frame(self.master)
        control_frame.pack(fill='x', padx=10, pady=5)

        self.voice_label = tk.Label(control_frame, text="音声:")
        self.voice_label.pack(side='left', padx=5)

        self.voice_combo = ttk.Combobox(control_frame, textvariable=self.voice_var)
        self.voice_combo['values'] = (
            "ja-JP-NanamiNeural",
            "ja-JP-KeitaNeural",
            "ja-JP-AoiNeural",
            "ja-JP-DaichiNeural",
            "ja-JP-MayuNeural",
            "ja-JP-NaokiNeural",
            "ja-JP-ShioriNeural"
        )
        self.voice_combo.pack(side='left', padx=5)

        button_frame = tk.Frame(self.master)
        button_frame.pack(fill='x', padx=10, pady=5)

        self.speak_button = tk.Button(button_frame, text="喋る", command=self.speak)
        self.speak_button.pack(side='left', padx=5)

        self.save_button = tk.Button(button_frame, text="音声保存", command=self.save_audio)
        self.save_button.pack(side='left', padx=5)

        self.clear_button = tk.Button(button_frame, text="クリア", command=self.clear)
        self.clear_button.pack(side='left', padx=5)

        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_azure_settings()
        self.load_saved_text()

    def speak(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "テキストを入力してください。")
            return

        speech_config = speechsdk.SpeechConfig(subscription=self.azure_key, region=self.azure_region)
        speech_config.speech_synthesis_voice_name = self.voice_var.get()

        text_chunks = self.split_text(text)
        num_chunks = len(text_chunks)
        self.progress_bar["maximum"] = num_chunks
        self.progress_bar["value"] = 0

        for chunk in text_chunks:
            result = speechsdk.SpeechSynthesizer(speech_config=speech_config).speak_text_async(chunk).get()
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                messagebox.showerror("エラー", f"音声合成に失敗しました: {result.reason}")
                return
            self.progress_bar["value"] += 1
            self.master.update_idletasks()

        messagebox.showinfo("成功", "テキストの読み上げが完了しました。")

    def save_audio(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "テキストを入力してください。")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                   filetypes=[("WAVファイル", "*.wav")],
                                                   title="音声ファイルを保存")
        if not file_path:
            return

        speech_config = speechsdk.SpeechConfig(subscription=self.azure_key, region=self.azure_region)
        speech_config.speech_synthesis_voice_name = self.voice_var.get()

        audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        text_chunks = self.split_text(text)
        num_chunks = len(text_chunks)
        self.progress_bar["maximum"] = num_chunks
        self.progress_bar["value"] = 0

        for chunk in text_chunks:
            result = speech_synthesizer.speak_text_async(chunk).get()
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                messagebox.showerror("エラー", f"音声合成に失敗しました: {result.reason}")
                return
            self.progress_bar["value"] += 1
            self.master.update_idletasks()

        messagebox.showinfo("成功", "音声ファイルの保存が完了しました。")

    def clear(self):
        self.text_input.delete("1.0", tk.END)

    def load_azure_settings(self):
        try:
            with open('setting.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.azure_key = settings['azure_key']
                self.azure_region = settings['azure_region']
        except FileNotFoundError:
            messagebox.showerror("エラー", "setting.jsonファイルが見つかりません。")
            self.master.quit()
        except json.JSONDecodeError:
            messagebox.showerror("エラー", "setting.jsonファイルの形式が正しくありません。")
            self.master.quit()
        except KeyError as e:
            messagebox.showerror("エラー", f"setting.jsonファイルに必要な設定 {e} がありません。")
            self.master.quit()

    def load_window_settings(self):
        try:
            with open('work.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if 'voice' in settings:
                    self.voice_var.set(settings['voice'])
                return f"{settings['width']}x{settings['height']}+{settings['x']}+{settings['y']}"
        except FileNotFoundError:
            return "400x300"
        except json.JSONDecodeError:
            os.remove('work.json')
            return "400x300"

    def save_window_settings(self):
        settings = {
            'width': self.master.winfo_width(),
            'height': self.master.winfo_height(),
            'x': self.master.winfo_x(),
            'y': self.master.winfo_y(),
            'text': self.text_input.get("1.0", tk.END).strip(),
            'voice': self.voice_var.get()
        }
        with open('work.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def load_saved_text(self):
        try:
            with open('work.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if 'text' in settings:
                    self.text_input.insert(tk.END, settings['text'])
                if 'voice' in settings:
                    self.voice_var.set(settings['voice'])
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            os.remove('work.json')

    def on_closing(self):
        self.save_window_settings()
        self.master.destroy()

    def split_text(self, text):
        # テキストを「。」や「、」で分割する
        return [chunk.strip() for chunk in text.replace('。', '。|').replace('、', '、|').split('|') if chunk]

if __name__ == "__main__":
    root = tk.Tk()
    app = TextToSpeechApp(root)
    root.mainloop()

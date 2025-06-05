# Conteúdo do arquivo predict_script.py
import argparse
import librosa
import numpy as np
from tensorflow.keras.models import load_model
import os


def main(args):
    new_model = load_model(args.model)

    data, sampling_rate = librosa.load(args.audio, duration=3, offset=0.5)

    mfcc = np.mean(librosa.feature.mfcc(
        y=data, sr=sampling_rate, n_mfcc=40).T, axis=0)

    mfcc = np.expand_dims(mfcc, axis=0)
    mfcc = np.expand_dims(mfcc, axis=-1)

    predictions = new_model.predict(mfcc)

    predicted_class = np.argmax(predictions)
    if predicted_class == 1:
        predicted_class = 'neutral'
    elif predicted_class == 3:
        predicted_class = 'happy'
    elif predicted_class == 5:
        predicted_class = 'angry'
    else:
        predicted_class = 'neutral'

    if os.path.isdir(args.output):
        output_path = os.path.join(args.output, 'class.txt')
    else:
        output_path = args.output

    try:
        with open(output_path, 'w') as file:
            file.write(str(predicted_class))
            print("wrote class.txt OK")
    except:
        print("error in creating file class.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='SER predictions.')

    parser.add_argument('--model', type=str,
                        help='SER model path.')

    parser.add_argument('--audio', type=str,
                        help='audio file path.')

    parser.add_argument(
        '--output', type=str, help='output path.')

    args = parser.parse_args()
    main(args)

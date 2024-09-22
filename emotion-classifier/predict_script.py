# Conteúdo do arquivo predict_script.py
import argparse
import librosa
import numpy as np
from tensorflow.keras.models import load_model
import os
# C:\Users\ferni>python C:\Users\ferni\Documents\maya\2022\scripts\emotion-classifier\predict_script.py --model C:\Users\ferni\Documents\SpeechEmotionRecognition\SER_model1.h5 --audio C:\Users\ferni\Downloads\test\in\a.wav --output C:\Users\ferni\Downloads\test\


def main(args):
    # Carregar o modelo treinado
    new_model = load_model(args.model)

    # Carregar um arquivo de áudio para teste
    data, sampling_rate = librosa.load(args.audio, duration=3, offset=0.5)

    # Extrair características (MFCC)
    mfcc = np.mean(librosa.feature.mfcc(
        y=data, sr=sampling_rate, n_mfcc=40).T, axis=0)

    # Pré-processar os dados (redimensionar e normalizar)
    mfcc = np.expand_dims(mfcc, axis=0)
    mfcc = np.expand_dims(mfcc, axis=-1)

    # Fazer predições
    predictions = new_model.predict(mfcc)

    # Obter a classe prevista (índice da maior probabilidade)
    predicted_class = np.argmax(predictions)
    if predicted_class == 1:
        predicted_class = 'neutral'
    elif predicted_class == 3:
        predicted_class = 'happy'
    elif predicted_class == 5:
        predicted_class = 'angry'
    else:
        predicted_class = 'neutral'

    # Verificar se o argumento output é um diretório
    if os.path.isdir(args.output):
        # Se for um diretório, criar o arquivo class.txt dentro dele
        output_path = os.path.join(args.output, 'class.txt')
    else:
        # Se for um caminho de arquivo, usar diretamente
        output_path = args.output

    # Salvar a classe prevista no caminho especificado pelo argumento 'output'
    try:
        with open(output_path, 'w') as file:
            file.write(str(predicted_class))
            print("wrote class.txt OK")
    except:
        print("error in creating file class.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Realizar previsões usando um modelo treinado.')

    # Argumento para o caminho do modelo
    parser.add_argument('--model', type=str,
                        help='Caminho para o modelo treinado.')

    # Argumento para o caminho do arquivo de áudio
    parser.add_argument('--audio', type=str,
                        help='Caminho para o arquivo de áudio de teste.')

    # Argumento para o caminho do arquivo de saída
    parser.add_argument(
        '--output', type=str, help='Caminho para salvar o arquivo com a classe prevista.')

    args = parser.parse_args()
    main(args)

import os
import json
import string
from underthesea import word_tokenize
import random
import shutil

json_folder = "split_data/test"
txt_folder = "txt/test"
source_folder = "Dataset"
train_folder = "split_data/train"
test_folder = "split_data/test"

def read_json(dir):
    with open(dir, 'r') as f:
        article_data = json.load(f)
    if 'maintext' in article_data:
        return article_data['maintext']
    elif 'text' in article_data:
        return article_data['text']
    else:
        raise KeyError("Neither 'maintext' nor 'text' found in the JSON file.")


def tokenize_file(json_dir, txt_dir):
    text = read_json(json_dir)
    with open(txt_dir, 'w') as f:
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        text = text.lower().replace('\n', ' ')
        text = word_tokenize(text, format='text')
        f.write(text)

def tokenize_folder(json_folder, txt_folder):
    # Process each file in the input folder
    for filename in os.listdir(json_folder):
        json_fp = os.path.join(json_folder, filename)
        txt_fp = os.path.join(txt_folder, filename.replace('.json', '.txt'))
        tokenize_file(json_fp, txt_fp)

def split_data(source, train, test, split_ratio=(0.8, 0.2)):
    files = os.listdir(source)
    random.shuffle(files)

    train_split = int(len(files) * split_ratio[0])

    train_files = files[:train_split]
    test_files = files[train_split:]

    for file in train_files:
        shutil.move(os.path.join(source, file), os.path.join(train, file))
    for file in test_files:
        shutil.move(os.path.join(source, file), os.path.join(test, file))



#!/usr/bin/env python3
"""
infer.py
簡單推論單張圖片
用法:
  python infer.py --model-path checkpoints/best.pth --img-path sample.jpg --labels-file labels.txt
如果沒有 labels.txt，程式會從 checkpoint 讀 classes
"""
import argparse
from PIL import Image
import torch
from torchvision import transforms
import timm
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--img-path", required=True)
    parser.add_argument("--img-size", type=int, default=224)
    args = parser.parse_args()

    ck = torch.load(args.model_path, map_location="cpu")
    classes = ck.get("classes", None)
    if classes is None:
        raise RuntimeError("No classes found in checkpoint")
    num_classes = len(classes)
    model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=num_classes)
    model.load_state_dict(ck["model_state"])
    model.eval()

    tf = transforms.Compose([
        transforms.Resize((args.img_size, args.img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    img = Image.open(args.img_path).convert("RGB")
    x = tf(img).unsqueeze(0)
    with torch.no_grad():
        out = model(x)
        probs = torch.softmax(out, dim=1).cpu().numpy()[0]
    top_idx = np.argsort(probs)[::-1][:5]
    for i in top_idx:
        print(f"{classes[i]}: {probs[i]:.4f}")

if __name__ == "__main__":
    main()



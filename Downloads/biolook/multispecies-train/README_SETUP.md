Multispecies Image Classifier - Setup & Run

1) 建立 Python 虛擬環境：
   python3 -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows (PowerShell)

2) 安裝套件：
   pip install -r requirements.txt

3) 下載資料（以 "taxa_list.txt" 指定要抓的物種或關鍵詞，每個一行）：
   mkdir -p data
   python tools/download_inat.py --taxa-file taxa_list.txt --out data --per-species 500 --val-split 0.2

   (會把每個物種的圖下載到 data/train/<label>/ 和 data/val/<label>/)

4) 開始訓練（用 GPU 建議）：
   python train.py --data-dir data --epochs 20 --batch-size 32 --model efficientnet_b3 --img-size 224 --lr 1e-4

5) 推論單張圖片：
   python infer.py --model-path checkpoints/best.pth --img-path sample.jpg --labels-file labels.txt

注意：
- 下載圖像來自 iNaturalist API，請注意 API 速率限制與資料授權。
- 訓練需要 GPU（推薦 NVIDIA），若在無 GPU 的機器也能跑，但非常慢。



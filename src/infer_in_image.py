import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from tracknet import BallTrackerNet

from homography import get_trans_matrix, refer_kps
from postprocess import postprocess, refine_kps

if __name__ == '__main__':

    print("Start inferring tennis court in image")

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, help='path to model')
    parser.add_argument('--input_path', type=str, help='path to input image')
    parser.add_argument('--output_path', type=str, help='path to output image')
    parser.add_argument('--output_csv', type=str, default=None, help='path to output court points to csv')
    parser.add_argument('--use_refine_kps', action='store_true', help='whether to use refine kps postprocessing')
    parser.add_argument('--use_homography', action='store_true', help='whether to use homography postprocessing')
    args = parser.parse_args()

    model = BallTrackerNet(out_channels=15)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.eval()

    OUTPUT_WIDTH = 640
    OUTPUT_HEIGHT = 360

    image = cv2.imread(args.input_path)
    img = cv2.resize(image, (OUTPUT_WIDTH, OUTPUT_HEIGHT))
    inp = (img.astype(np.float32) / 255.)
    inp = torch.tensor(np.rollaxis(inp, 2, 0))
    inp = inp.unsqueeze(0)

    out = model(inp.float().to(device))[0]
    pred = F.sigmoid(out).detach().cpu().numpy()

    points = []
    for kps_num in range(14):
        heatmap = (pred[kps_num]*255).astype(np.uint8)
        x_pred, y_pred = postprocess(heatmap, low_thresh=170, max_radius=25)
        if args.use_refine_kps and kps_num not in [8, 12, 9] and x_pred and y_pred:
            x_pred, y_pred = refine_kps(image, int(y_pred), int(x_pred))
        x_pred = x_pred // 2
        y_pred = y_pred // 2
        points.append((x_pred, y_pred))

    if args.use_homography:
        matrix_trans = get_trans_matrix(points)
        if matrix_trans is not None:
            points = cv2.perspectiveTransform(refer_kps, matrix_trans)
            points = [np.squeeze(x) for x in points]

    if args.output_csv is not None:
        points_ndarray = np.vstack(points) # 14 x 2
        df_data = {
            "X": points_ndarray[:,0],
            "Y": points_ndarray[:,1],
        }
        df = pd.DataFrame.from_dict(df_data)
        Path(args.output_csv).parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(str(args.output_csv), index=False)

    for j in range(len(points)):
        if points[j][0] is not None:
            image = cv2.circle(image, (int(points[j][0]), int(points[j][1])),
                               radius=0, color=(0, 0, 255), thickness=10)

    cv2.imwrite(args.output_path, image)

# ComfyUI Pixel Scaling

一个用于 ComfyUI 的 K-Centroid 图片缩小节点，算法基于
[Astropulse/pixeldetector 的 `k-centroid-only` 分支](https://github.com/Astropulse/pixeldetector/tree/k-centroid-only)。

K-Centroid 会把每个目标像素对应的源图区域作为一个 tile，使用 K-Means
把 tile 的颜色聚成若干类，再选择出现次数最多的聚类颜色作为目标像素。
它适合把普通图片缩成像素画尺寸，并减少传统插值产生的模糊。

## 环境要求

- Python 3.13
- ComfyUI（提供 PyTorch）
- NumPy 2.1+
- Pillow 11+

项目使用 [uv](https://docs.astral.sh/uv/) 管理开发环境，同时提供
`requirements.txt` 给 ComfyUI 使用。

## 安装到 ComfyUI

把项目放入 `ComfyUI/custom_nodes/comfyui-pixel-scaling`，然后在 ComfyUI
的 Python 环境中安装依赖：

```bash
cd ComfyUI/custom_nodes/comfyui-pixel-scaling
python -m pip install -r requirements.txt
```

重启 ComfyUI，在 `image/transform` 分类中添加
`K-Centroid Downscale`。

## 节点参数

- `image`：ComfyUI `IMAGE`，支持批量输入和内嵌 RGBA。
- `mask`：可选的 ComfyUI `MASK`。标准 `Load Image` 节点会把 PNG Alpha
  作为 MASK 输出，可直接连接到这里。
- `width` / `height`：输出尺寸。K-Centroid 只用于缩小，因此两个值都不能
  超过输入尺寸。
- `centroids`：每个 tile 的聚类数量，默认为 `2`。数值越大越可能保留细微
  颜色，但计算量也会增加。

节点输出缩小后的 `IMAGE` 和 `MASK`。RGB 通道按上游算法处理；RGBA
输入的 Alpha，或单独连接的 MASK，都会使用相同的 K-Centroid tile
聚类方式缩小，以保留透明区域的硬边。RGBA 输入仍输出 RGBA，RGB 输入
仍输出 RGB；没有透明信息时，MASK 输出为全黑。

## 使用 uv 开发

```bash
uv sync
```

依赖修改后，重新生成 ComfyUI 使用的依赖文件：

```bash
uv lock
uv export --no-dev --no-hashes --no-header --no-emit-project \
  -o requirements.txt
```

## 许可证与致谢

K-Centroid 算法来自 Astropulse/pixeldetector，原项目采用 MIT License。
本项目保留其版权与许可声明，详见 `LICENSE`。

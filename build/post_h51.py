"""post_h51.py: renders/raw/*.png -> renders/*.jpg. Bloom on the highlights, a soft S-curve, warm highlights, a light vignette, fine grain.
Run: python3 build/post_h51.py [name ...]"""
import os, sys, numpy as np
from PIL import Image, ImageFilter
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'renders'); RAW = os.path.join(R, 'raw')
def grade(src, dst, plan=False):
    im = Image.open(src).convert('RGB'); w, h = im.size; a = np.asarray(im).astype(np.float32) / 255
    if not plan:
        lum = a.max(axis=2); mask = np.clip((lum - 0.80) / 0.20, 0, 1)[..., None]
        bl = Image.fromarray((a * mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=w / 110)); bl2 = Image.fromarray((a * mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=w / 30))
        a = np.clip(a + 0.22 * np.asarray(bl).astype(np.float32) / 255 + 0.16 * np.asarray(bl2).astype(np.float32) / 255, 0, 1)
        s = a * a * (3 - 2 * a); a = a * 0.6 + s * 0.4
        a[..., 0] *= 1.015; a[..., 2] *= 0.985
        yy, xx = np.mgrid[0:h, 0:w]; r = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2; a *= (1 - 0.16 * np.clip(r - 0.25, 0, 1.2))[..., None]
        a += np.random.default_rng(7).normal(0, 0.010, a.shape).astype(np.float32)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(dst, quality=93, subsampling=0)
if __name__ == '__main__':
    names = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(RAW) if f.endswith('.png'))
    for n in names: grade(os.path.join(RAW, n + '.png'), os.path.join(R, n + '.jpg'), plan=('plan' in n)); print('graded', n)

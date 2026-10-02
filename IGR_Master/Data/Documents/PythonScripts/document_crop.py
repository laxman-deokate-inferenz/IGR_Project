import cv2
import numpy as np
from pathlib import Path
import traceback


def order_points(pts):
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    try:
        rect = order_points(pts)
        (tl, tr, br, bl) = rect

        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)
        maxHeight = max(int(heightA), int(heightB))

        if maxWidth < 50 or maxHeight < 50:
            return None

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    except:
        return None


def detect_card(image):
    try:
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        best_pts = None
        max_score = 0

        for thresh in range(140, 230, 15):
            _, binary = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < w * h * 0.05:
                    continue

                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

                if len(approx) == 4:
                    pts = approx.reshape(4, 2)
                    x, y, bw, bh = cv2.boundingRect(pts)
                    aspect = max(bw, bh) / max(min(bw, bh), 1)

                    if 1.25 <= aspect <= 2.3:
                        score = area
                        if score > max_score:
                            max_score = score
                            best_pts = pts
        return best_pts
    except:
        return None


def mild_crop(image, pad=10):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        coords = cv2.findNonZero(binary)
        if coords is None:
            return image

        x, y, w, h = cv2.boundingRect(coords)
        x = max(0, x - pad)
        y = max(0, y - pad)
        w = min(image.shape[1] - x, w + 2 * pad)
        h = min(image.shape[0] - y, h + 2 * pad)
        return image[y:y+h, x:x+w]
    except:
        return image


def crop_document(input_path, output_path):
    """
    Main function for UiPath
    """
    try:
        input_path = str(input_path)
        output_path = str(output_path)

        print("Starting crop...")
        print("Input :", input_path)
        print("Output:", output_path)

        image = cv2.imread(input_path)
        if image is None:
            print("ERROR: Cannot read image")
            return "ERROR_CANNOT_READ_IMAGE"

        original = image.copy()
        h, w = original.shape[:2]
        print(f"Original size: {w}x{h}")

        # Resize for detection
        max_dim = 1000
        scale = min(max_dim / max(h, w), 1.0)

        if scale < 1.0:
            small = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        else:
            small = image.copy()
            scale = 1.0

        pts = detect_card(small)

        if pts is not None:
            if scale != 1.0:
                pts = pts / scale

            print("Card corners found")
            warped = four_point_transform(original, pts)

            if warped is not None:
                final = mild_crop(warped, pad=8)
                cv2.imwrite(output_path, final)
                print("SUCCESS - Perspective crop done")
                return "SUCCESS"

        # Fallback
        print("Using fallback crop")
        final = mild_crop(original, pad=20)
        cv2.imwrite(output_path, final)
        print("SUCCESS - Fallback crop done")
        return "SUCCESS"

    except Exception as e:
        print("EXCEPTION OCCURRED:")
        print(str(e))
        print(traceback.format_exc())
        return "ERROR: " + str(e)


# For testing outside UiPath
if __name__ == "__main__":
    input_file  = r"C:\Users\DeokateLaxman\Documents\UiPathAutomation\IGR_Master\Data\Input\00.jpeg"
    output_file = r"C:\Users\DeokateLaxman\Documents\UiPathAutomation\IGR_Master\Data\Input\21122_cropped.jpeg"
    
    result = crop_document(input_file, output_file)
    print("Result:", result)
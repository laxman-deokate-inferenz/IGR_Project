import cv2
import numpy as np
import math


# ============================================================
# ORDER 4 CORNERS
# ============================================================

def order_points(points):

    points = np.array(points, dtype="float32")

    result = np.zeros((4, 2), dtype="float32")

    s = points.sum(axis=1)

    result[0] = points[np.argmin(s)]   # Top-left
    result[2] = points[np.argmax(s)]   # Bottom-right

    diff = np.diff(points, axis=1)

    result[1] = points[np.argmin(diff)]   # Top-right
    result[3] = points[np.argmax(diff)]   # Bottom-left

    return result


# ============================================================
# PERSPECTIVE TRANSFORM
# ============================================================

def four_point_transform(image, points):

    rect = order_points(points)

    tl, tr, br, bl = rect

    width1 = np.linalg.norm(br - bl)
    width2 = np.linalg.norm(tr - tl)

    height1 = np.linalg.norm(tr - br)
    height2 = np.linalg.norm(tl - bl)

    max_width = int(max(width1, width2))
    max_height = int(max(height1, height2))

    if max_width <= 0 or max_height <= 0:
        return image

    destination = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(
        rect,
        destination
    )

    return cv2.warpPerspective(
        image,
        matrix,
        (max_width, max_height)
    )


# ============================================================
# VALIDATE DOCUMENT
# ============================================================

def validate_document(points, image_width, image_height):

    points = np.array(points, dtype="float32")

    x, y, w, h = cv2.boundingRect(
        points.astype(np.int32)
    )

    image_area = image_width * image_height
    bounding_area = w * h

    if bounding_area <= 0:
        return False, 0

    area_ratio = bounding_area / image_area

    # Reject tiny objects
    if area_ratio < 0.12:
        return False, 0

    # Document should have reasonable size
    if w < image_width * 0.30:
        return False, 0

    if h < image_height * 0.10:
        return False, 0

    # Calculate polygon area
    polygon_area = cv2.contourArea(
        points.astype(np.float32)
    )

    if polygon_area <= 0:
        return False, 0

    rectangularity = polygon_area / bounding_area

    if rectangularity < 0.50:
        return False, 0

    # QR codes are normally square
    aspect = max(w, h) / max(
        min(w, h),
        1
    )

    if aspect < 1.20 and area_ratio < 0.50:
        return False, 0

    score = (
        polygon_area *
        rectangularity *
        (1 + area_ratio)
    )

    return True, score


# ============================================================
# CONTOUR METHOD
# ============================================================

def contour_detection(image):

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    candidates = []

    # --------------------------------------------------------
    # Multiple edge settings
    # --------------------------------------------------------

    for low, high in [
        (20, 80),
        (30, 100),
        (40, 120),
        (50, 150)
    ]:

        edges = cv2.Canny(
            gray,
            low,
            high
        )

        # Connect broken document borders
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (11, 11)
        )

        edges = cv2.morphologyEx(
            edges,
            cv2.MORPH_CLOSE,
            kernel
        )

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:

            area = cv2.contourArea(contour)

            if area < (width * height * 0.12):
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            if perimeter == 0:
                continue

            # Try different approximation levels
            for epsilon_factor in [
                0.015,
                0.020,
                0.025,
                0.030,
                0.040
            ]:

                approx = cv2.approxPolyDP(
                    contour,
                    epsilon_factor * perimeter,
                    True
                )

                if len(approx) != 4:
                    continue

                points = approx.reshape(
                    4,
                    2
                )

                valid, score = validate_document(
                    points,
                    width,
                    height
                )

                if valid:

                    candidates.append(
                        (
                            score,
                            points
                        )
                    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print(
        "CONTOUR DOCUMENT FOUND"
    )

    return candidates[0][1]


# ============================================================
# BRIGHT DOCUMENT METHOD
# ============================================================

def bright_document_detection(image):

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    candidates = []

    for threshold_value in [
        170,
        180,
        190,
        200,
        210,
        220
    ]:

        _, binary = cv2.threshold(
            gray,
            threshold_value,
            255,
            cv2.THRESH_BINARY
        )

        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (21, 21)
        )

        binary = cv2.morphologyEx(
            binary,
            cv2.MORPH_CLOSE,
            kernel
        )

        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:

            area = cv2.contourArea(
                contour
            )

            if area < width * height * 0.12:
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            if perimeter == 0:
                continue

            approx = cv2.approxPolyDP(
                contour,
                0.025 * perimeter,
                True
            )

            if len(approx) != 4:
                continue

            points = approx.reshape(
                4,
                2
            )

            valid, score = validate_document(
                points,
                width,
                height
            )

            if valid:

                candidates.append(
                    (
                        score * 1.10,
                        points
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print(
        "BRIGHT DOCUMENT FOUND"
    )

    return candidates[0][1]


# ============================================================
# HOUGH LINE METHOD
# ============================================================

def hough_document_detection(image):

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edges = cv2.Canny(
        gray,
        30,
        120
    )

    # Connect border edges
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (7, 7)
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=60,
        minLineLength=int(
            max(width, height) * 0.25
        ),
        maxLineGap=30
    )

    if lines is None:
        return None

    horizontal = []
    vertical = []

    for line in lines:

        x1, y1, x2, y2 = line[0]

        dx = x2 - x1
        dy = y2 - y1

        length = math.sqrt(
            dx * dx +
            dy * dy
        )

        angle = math.degrees(
            math.atan2(
                dy,
                dx
            )
        )

        # Normalize angle
        if angle < -90:
            angle += 180

        if angle > 90:
            angle -= 180

        # Horizontal-ish
        if abs(angle) <= 30:

            horizontal.append(
                (
                    length,
                    x1,
                    y1,
                    x2,
                    y2,
                    angle
                )
            )

        # Vertical-ish
        elif abs(angle) >= 60:

            vertical.append(
                (
                    length,
                    x1,
                    y1,
                    x2,
                    y2,
                    angle
                )
            )

    # Need at least two lines in each direction
    if len(horizontal) < 2:
        return None

    if len(vertical) < 2:
        return None

    horizontal.sort(
        reverse=True
    )

    vertical.sort(
        reverse=True
    )

    # Take several strongest lines
    horizontal = horizontal[:10]
    vertical = vertical[:10]

    candidates = []

    # --------------------------------------------------------
    # Create intersections
    # --------------------------------------------------------

    def line_intersection(line1, line2):

        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2

        denominator = (
            (x1 - x2) * (y3 - y4)
            -
            (y1 - y2) * (x3 - x4)
        )

        if abs(denominator) < 0.0001:
            return None

        px = (
            (x1 * y2 - y1 * x2) *
            (x3 - x4)
            -
            (x1 - x2) *
            (x3 * y4 - y3 * x4)
        ) / denominator

        py = (
            (x1 * y2 - y1 * x2) *
            (y3 - y4)
            -
            (y1 - y2) *
            (x3 * y4 - y3 * x4)
        ) / denominator

        return np.array(
            [px, py],
            dtype="float32"
        )

    # --------------------------------------------------------
    # Try combinations
    # --------------------------------------------------------

    for i in range(
        len(horizontal)
    ):

        for j in range(
            i + 1,
            len(horizontal)
        ):

            h1 = horizontal[i]
            h2 = horizontal[j]

            for k in range(
                len(vertical)
            ):

                for l in range(
                    k + 1,
                    len(vertical)
                ):

                    v1 = vertical[k]
                    v2 = vertical[l]

                    line_h1 = h1[1:5]
                    line_h2 = h2[1:5]

                    line_v1 = v1[1:5]
                    line_v2 = v2[1:5]

                    p1 = line_intersection(
                        line_h1,
                        line_v1
                    )

                    p2 = line_intersection(
                        line_h1,
                        line_v2
                    )

                    p3 = line_intersection(
                        line_h2,
                        line_v2
                    )

                    p4 = line_intersection(
                        line_h2,
                        line_v1
                    )

                    if (
                        p1 is None
                        or p2 is None
                        or p3 is None
                        or p4 is None
                    ):
                        continue

                    points = np.array(
                        [
                            p1,
                            p2,
                            p3,
                            p4
                        ],
                        dtype="float32"
                    )

                    # Check points are inside image
                    if np.any(points[:, 0] < -20):
                        continue

                    if np.any(points[:, 0] > width + 20):
                        continue

                    if np.any(points[:, 1] < -20):
                        continue

                    if np.any(points[:, 1] > height + 20):
                        continue

                    valid, score = validate_document(
                        points,
                        width,
                        height
                    )

                    if not valid:
                        continue

                    line_score = (
                        h1[0]
                        +
                        h2[0]
                        +
                        v1[0]
                        +
                        v2[0]
                    )

                    final_score = (
                        score *
                        line_score
                    )

                    candidates.append(
                        (
                            final_score,
                            points
                        )
                    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print(
        "HOUGH DOCUMENT FOUND"
    )

    return candidates[0][1]


# ============================================================
# FALLBACK
# ============================================================

def fallback_crop(image, output_path):

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Try Otsu
    # --------------------------------------------------------

    _, threshold = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV +
        cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (25, 25)
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    best_rect = None
    best_area = 0

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if area < width * height * 0.15:
            continue

        if w < width * 0.30:
            continue

        if h < height * 0.10:
            continue

        if area > best_area:

            best_area = area

            best_rect = (
                x,
                y,
                w,
                h
            )

    if best_rect is not None:

        x, y, w, h = best_rect

        cropped = image[
            y:y + h,
            x:x + w
        ]

        cv2.imwrite(
            output_path,
            cropped
        )

        print(
            "FALLBACK CROP SUCCESS:",
            output_path
        )

        return output_path

    # --------------------------------------------------------
    # Nothing detected
    # --------------------------------------------------------

    cv2.imwrite(
        output_path,
        image
    )

    print(
        "NO CROP POSSIBLE - ORIGINAL SAVED"
    )

    return output_path


# ============================================================
# MAIN DOCUMENT CROP
# ============================================================

def crop_document(
    input_path,
    output_path
):

    print("")
    print(
        "======================================"
    )
    print(
        "DOCUMENT CROP STARTED"
    )
    print(
        "INPUT:",
        input_path
    )
    print(
        "OUTPUT:",
        output_path
    )
    print(
        "======================================"
    )

    image = cv2.imread(
        input_path
    )

    if image is None:

        raise Exception(
            "Unable to read image: "
            + input_path
        )

    original = image.copy()

    original_height, original_width = (
        image.shape[:2]
    )

    print(
        "ORIGINAL SIZE:",
        original_width,
        "x",
        original_height
    )

    # ========================================================
    # RESIZE FOR DETECTION
    # ========================================================

    max_dimension = 1400

    scale = min(
        max_dimension /
        max(
            original_height,
            original_width
        ),
        1.0
    )

    if scale < 1.0:

        small = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )

    else:

        small = image.copy()

        scale = 1.0

    # ========================================================
    # METHOD 1 - CONTOUR
    # ========================================================

    best = contour_detection(
        small
    )

    method = "CONTOUR"

    # ========================================================
    # METHOD 2 - BRIGHT DOCUMENT
    # ========================================================

    if best is None:

        best = bright_document_detection(
            small
        )

        method = "BRIGHT"

    # ========================================================
    # METHOD 3 - HOUGH LINES
    # ========================================================

    if best is None:

        best = hough_document_detection(
            small
        )

        method = "HOUGH"

    # ========================================================
    # PERSPECTIVE CROP
    # ========================================================

    if best is not None:

        # Convert coordinates to original image
        if scale != 1.0:

            best = best / scale

        print(
            "SELECTED METHOD:",
            method
        )

        print(
            "DOCUMENT CORNERS:"
        )

        print(best)

        cropped = four_point_transform(
            original,
            best
        )

        if cropped is not None:

            crop_height, crop_width = (
                cropped.shape[:2]
            )

            original_area = (
                original_width *
                original_height
            )

            cropped_area = (
                crop_width *
                crop_height
            )

            crop_ratio = (
                cropped_area /
                original_area
            )

            print(
                "CROPPED SIZE:",
                crop_width,
                "x",
                crop_height
            )

            print(
                "CROP AREA RATIO:",
                crop_ratio
            )

            # Safety protection
            if crop_ratio >= 0.12:

                cv2.imwrite(
                    output_path,
                    cropped
                )

                print(
                    "CROP SUCCESS:",
                    output_path
                )

                print(
                    "======================================"
                )

                return output_path

            else:

                print(
                    "CROP REJECTED - TOO SMALL"
                )

    # ========================================================
    # FALLBACK
    # ========================================================

    print(
        "NO RELIABLE 4-CORNER DOCUMENT FOUND"
    )

    return fallback_crop(
        original,
        output_path
    )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    input_file = r"C:\Users\DeokateLaxman\Documents\UiPathAutomation\IGR_Master\Data\Input\Screenshot 2026-09-19 025012.jpeg"

    output_file = r"C:\Users\DeokateLaxman\Documents\UiPathAutomation\IGR_Master\Data\Input\22_cropped.jpeg"

    crop_document(
        input_file,
        output_file
    )
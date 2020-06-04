import subprocess
import time

orca_next_path = "/media/jmmease/SSD1/orca-next/repos/build/orca_next/orca_next"

proc = subprocess.Popen(
    [orca_next_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

def to_image(fig, format="png", width=700, height=500, scale=1, timeout=20):
    import json
    import base64
    export_spec = f'{{"figure": {fig}, "format": "{format}", "width": {width}, "height": {height}, "scale": {scale}}}\n'.encode('utf-8')

    # Write and flush spec
    proc.stdin.writelines([export_spec])
    proc.stdin.flush()
    response = json.loads(proc.stdout.readline().decode('utf-8'))
    img_string = response['result']

    if img_string is None:
        raise ValueError(response)

    if format == 'svg':
        img = img_string.encode()
    else:
        img = base64.decodebytes(img_string.encode())
    return img


if __name__ == "__main__":
    time.sleep(2)
    fig_json = '{"data":[{"y":[1,3,2], "name":"asdf another"}]}'

    t0 = time.time()
    imgs = []
    for format in ['png', 'svg', 'jpeg']:
        img = to_image(fig_json, format=format, width=700, height=500, scale=1, timeout=20)
        imgs.append(img)
        print(img)
        with open(f'../tmp.{format}', 'wb') as f:
            f.write(img)

    t1 = time.time()
    print(f"time: {t1 - t0}")
#!/usr/bin/env python3
"""
sBotics Robots CLI — Ferramenta para manipulação, validação, descriptografia e criptografia de robôs (.sBot).
"""

import os
import sys
import json
import base64
import hmac
import hashlib
import argparse
import subprocess
from typing import Dict, Any, Tuple, List

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
except ImportError:
    print("Erro: A biblioteca 'cryptography' é necessária. Instale com: pip install cryptography", file=sys.stderr)
    sys.exit(1)

KEY_BASE64 = "JCZWRVPvlhQ0iSkIIxqeRyE6TFWHg6f2qP1tbK0del8="
KEY_BYTES = base64.b64decode(KEY_BASE64)

VALID_PLACEABLES = {
    "Cube", "Wedge", "Hinge", "SmallWheel", "LargeWheel", "Buzzer",
    "Light", "Servomotor", "ColorSensor", "UltrasonicSensor", "TouchSensor",
    "Slab", "Camera", "Pen", "Pyramid", "WedgeColorSensor", "WedgeUltrasonicSensor", "Corner"
}

CORE_WEIGHT = 1.0

PLACEABLE_WEIGHTS: Dict[str, float] = {
    "Servomotor": 2.00,
    "LargeWheel": 1.50,
    "Cube": 1.00,
    "ColorSensor": 1.00,
    "UltrasonicSensor": 1.00,
    "TouchSensor": 1.00,
    "Camera": 1.00,
    "Buzzer": 1.00,
    "Pen": 1.00,
    "SmallWheel": 0.75,
    "Light": 0.75,
    "Pyramid": 0.66,
    "Wedge": 0.50,
    "Slab": 0.50,
    "WedgeColorSensor": 0.50,
    "WedgeUltrasonicSensor": 0.50,
    "Corner": 0.35,
    "Hinge": 0.25,
}

VALID_MATERIALS = {
    "ColorWhite", "ColorGray", "ColorDarkGray", "ColorBlack",
    "ColorGreen", "ColorLime", "ColorTeal", "ColorCyan",
    "ColorBlue", "ColorPurple", "ColorMagenta", "ColorPink",
    "ColorRed", "ColorBrown", "ColorOrange", "ColorYellow"
}


def decrypt_sbot(sbot_path: str) -> str:
    """Descriptografa um arquivo .sBot e retorna o JSON em texto."""
    if not os.path.exists(sbot_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {sbot_path}")

    with open(sbot_path, "r", encoding="utf-8-sig") as f:
        outer = json.load(f)

    raw_data = outer.get("data")
    if not raw_data:
        raise ValueError("O arquivo não possui o campo 'data'.")

    inner_json_bytes = base64.b64decode(raw_data)
    inner = json.loads(inner_json_bytes.decode("utf-8"))

    iv_b64 = inner.get("iv")
    val_b64 = inner.get("value")
    given_mac = inner.get("mac")

    iv_bytes = base64.b64decode(iv_b64)
    cipher_bytes = base64.b64decode(val_b64)

    # HMAC Verification
    mac_data = (iv_b64 + val_b64).encode("utf-8")
    computed_mac = hmac.new(KEY_BYTES, mac_data, hashlib.sha256).hexdigest().lower()

    if given_mac.lower() != computed_mac:
        print("[AVISO] Assinatura HMAC não coincide! O arquivo pode ter sido alterado ou corrompido.", file=sys.stderr)

    # AES-256-CBC Decryption
    cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(iv_bytes))
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(cipher_bytes) + decryptor.finalize()

    # PKCS7 Unpadding
    unpadder = padding.PKCS7(128).unpadder()
    plain_bytes = unpadder.update(padded_plain) + unpadder.finalize()

    return plain_bytes.decode("utf-8")


def encrypt_sbot(plain_json_str: str, robot_name: str) -> str:
    """Criptografa um JSON de robô e retorna o conteúdo formatado do arquivo .sBot."""
    # Garante que é um JSON válido
    robot_obj = json.loads(plain_json_str)
    name = robot_obj.get("name") or robot_name

    iv_bytes = os.urandom(16)
    iv_b64 = base64.b64encode(iv_bytes).decode("ascii")

    # PKCS7 Padding
    padder = padding.PKCS7(128).padder()
    plain_bytes = plain_json_str.encode("utf-8")
    padded_data = padder.update(plain_bytes) + padder.finalize()

    # AES-256-CBC Encryption
    cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(iv_bytes))
    encryptor = cipher.encryptor()
    cipher_bytes = encryptor.update(padded_data) + encryptor.finalize()
    val_b64 = base64.b64encode(cipher_bytes).decode("ascii")

    # HMAC-SHA256
    mac_data = (iv_b64 + val_b64).encode("utf-8")
    mac_hex = hmac.new(KEY_BYTES, mac_data, hashlib.sha256).hexdigest().lower()

    inner_dict = {"iv": iv_b64, "value": val_b64, "mac": mac_hex}
    inner_json_bytes = json.dumps(inner_dict).encode("utf-8")
    inner_b64 = base64.b64encode(inner_json_bytes).decode("ascii")

    outer = {"name": name, "data": inner_b64}
    return json.dumps(outer, separators=(',', ':'))


def calculate_physics(robot: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula peso total (Zg), Centro de Massa (CoM) e indicadores de equilíbrio do robô."""
    blocks = robot.get("blocks", [])
    # Inclui o Core fixo em (0, 0, 0) com 1.0 Zg
    total_weight = CORE_WEIGHT
    wx, wy, wz = 0.0, 0.0, 0.0

    min_x, max_x = 0.0, 0.0
    min_y, max_y = 0.0, 0.0
    min_z, max_z = 0.0, 0.0

    wheel_xs: List[float] = []
    wheel_zs: List[float] = []

    for b in blocks:
        b_type = b.get("type", "")
        pos = b.get("position", {})
        px = float(pos.get("x", 0))
        py = float(pos.get("y", 0))
        pz = float(pos.get("z", 0))

        w = PLACEABLE_WEIGHTS.get(b_type, 1.0)
        total_weight += w
        wx += px * w
        wy += py * w
        wz += pz * w

        min_x, max_x = min(min_x, px), max(max_x, px)
        min_y, max_y = min(min_y, py), max(max_y, py)
        min_z, max_z = min(min_z, pz), max(max_z, pz)

        if b_type in ("LargeWheel", "SmallWheel"):
            wheel_xs.append(px)
            wheel_zs.append(pz)

    com_x = wx / total_weight
    com_y = wy / total_weight
    com_z = wz / total_weight

    if wheel_xs:
        support_center_x = (min(wheel_xs) + max(wheel_xs)) / 2.0
        wheel_min_z, wheel_max_z = min(wheel_zs), max(wheel_zs)
    else:
        support_center_x = (min_x + max_x) / 2.0
        wheel_min_z, wheel_max_z = min_z, max_z

    lateral_offset = com_x - support_center_x
    balance_warnings: List[str] = []

    if abs(lateral_offset) > 0.25:
        side = "direita (+X)" if lateral_offset > 0 else "esquerda (-X)"
        balance_warnings.append(
            f"Desequilíbrio lateral detectado: Centro de Massa X ({com_x:.2f}) está deslocado em "
            f"{lateral_offset:+.2f} blocos para a {side} em relação ao centro das rodas ({support_center_x:.2f}). "
            "O robô pode puxar para o lado ou tombar em curvas."
        )

    if wheel_zs and (com_z > wheel_max_z + 0.3 or com_z < wheel_min_z - 0.3):
        dir_z = "frente (+Z)" if com_z > wheel_max_z else "trás (-Z)"
        balance_warnings.append(
            f"Desequilíbrio longitudinal: Centro de Massa Z ({com_z:.2f}) está fora da base de apoio das rodas "
            f"[{wheel_min_z:.1f}, {wheel_max_z:.1f}], pendendo para {dir_z}."
        )

    return {
        "total_weight": total_weight,
        "com": (com_x, com_y, com_z),
        "support_center_x": support_center_x,
        "lateral_offset": lateral_offset,
        "wheel_z_range": (wheel_min_z, wheel_max_z),
        "bounds": ((min_x, max_x), (min_y, max_y), (min_z, max_z)),
        "balance_warnings": balance_warnings,
    }


def validate_robot(robot: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, str]]:
    """Valida as restrições físicas e estruturais do robô para o sBotics."""
    errors = []
    warnings = []
    components = {}
    pos_map = set()

    blocks = robot.get("blocks", [])
    if not blocks:
        errors.append("O robô não possui blocos ('blocks' está vazio).")
        return errors, warnings, components

    for i, b in enumerate(blocks):
        b_type = b.get("type")
        pos = b.get("position")
        if not pos:
            errors.append(f"Bloco #{i} ('{b_type}') não possui coordenadas 'position'.")
            continue

        px, py, pz = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)
        key = (px, py, pz)
        pos_str = f"({px}, {py}, {pz})"
        pos_map.add(key)

        # Regra Crítica: (0,0,0) é do Core
        if px == 0 and py == 0 and pz == 0:
            errors.append(
                f"ERRO CRÍTICO: Nenhum bloco pode ser colocado na posição {pos_str}. "
                "Essa coordenada é reservada exclusivamente para o 'Core' (RobotController) da simulação. "
                "Peças conectadas a ele devem usar 'anchor': {'x': 0, 'y': 0, 'z': 0}."
            )

        # Bounding Box
        if not (-8 <= px <= 8):
            errors.append(f"Bloco em {pos_str} excede o limite X [-8, 8]: {px}")
        if not (-4 <= py <= 12):
            errors.append(f"Bloco em {pos_str} excede o limite Y [-4, 12]: {py}")
        if not (-8 <= pz <= 8):
            errors.append(f"Bloco em {pos_str} excede o limite Z [-8, 8]: {pz}")

        # Placeable
        if b_type not in VALID_PLACEABLES:
            errors.append(f"Tipo de bloco desconhecido '{b_type}' em {pos_str}.")

        # Material/Color
        color = b.get("color")
        if color and color not in VALID_MATERIALS:
            warnings.append(f"Material/cor desconhecido '{color}' em {pos_str}.")

        # Nome de componente
        name = b.get("name")
        if name:
            if name in components:
                errors.append(f"Nome de componente duplicado: '{name}' em {pos_str} e {components[name]}.")
            else:
                components[name] = pos_str

    # Verificação de âncoras (Joints)
    for b in blocks:
        pos = b.get("position", {})
        px, py, pz = pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)
        anchor = b.get("anchor")
        if anchor:
            ax, ay, az = anchor.get("x", 0), anchor.get("y", 0), anchor.get("z", 0)
            a_key = (ax, ay, az)
            p_key = (px, py, pz)
            if a_key != (0, 0, 0) and a_key != p_key and a_key not in pos_map:
                warnings.append(f"Bloco em ({px},{py},{pz}) tem 'anchor' ({ax},{ay},{az}) apontando para coordenada vazia.")

    physics = calculate_physics(robot)
    warnings.extend(physics["balance_warnings"])

    return errors, warnings, components


def cmd_decrypt(args):
    plain = decrypt_sbot(args.input)
    out_path = args.output or os.path.splitext(args.input)[0] + ".json"
    # Formata o JSON com indentação para facilitar leitura
    parsed = json.loads(plain)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)
    print(f"[OK] Descriptografado com sucesso! Arquivo salvo em: {out_path}")


def cmd_encrypt(args):
    with open(args.input, "r", encoding="utf-8-sig") as f:
        content = f.read()
    out_path = args.output or os.path.splitext(args.input)[0] + ".sBot"
    sbot_content = encrypt_sbot(content, args.name or "Robo")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sbot_content)
    print(f"[OK] Criptografado e assinado com sucesso! Arquivo salvo em: {out_path}")


def cmd_validate(args):
    path = args.input
    if path.lower().endswith(".sbot"):
        plain = decrypt_sbot(path)
        robot = json.loads(plain)
    else:
        with open(path, "r", encoding="utf-8-sig") as f:
            robot = json.load(f)

    errors, warnings, components = validate_robot(robot)
    physics = calculate_physics(robot)
    com_x, com_y, com_z = physics["com"]

    print("================ Relatório de Validação ================")
    print(f"Nome do Robô: {robot.get('name', 'Sem Nome')}")
    print(f"Total de Blocos: {len(robot.get('blocks', []))} (+1 Core = {len(robot.get('blocks', [])) + 1})")
    print(f"Peso Total Estimado: {physics['total_weight']:.2f} Zg")
    print(
        f"Centro de Massa (CoM): X={com_x:+.2f}, Y={com_y:+.2f}, Z={com_z:+.2f} "
        f"(Centro Lateral das Rodas X={physics['support_center_x']:+.2f}, Desvio Lateral={physics['lateral_offset']:+.2f})"
    )
    print(f"Componentes Nomeados ({len(components)}):")
    for name, pos in components.items():
        print(f"  - {name:20} -> {pos}")

    if warnings:
        print(f"\nAvisos ({len(warnings)}):")
        for w in warnings:
            print(f"  [!] {w}")

    if errors:
        print(f"\nErros Críticos ({len(errors)}):")
        for e in errors:
            print(f"  [X] {e}")
        print("\nStatus: INVÁLIDO PARA A PLATAFORMA SBOTICS!")
        sys.exit(1)
    else:
        print("\nStatus: VÁLIDO E COMPATÍVEL COM O SBOTICS! (100% íntegro)")


def cmd_info(args):
    path = args.input
    if path.lower().endswith(".sbot"):
        plain = decrypt_sbot(path)
        robot = json.loads(plain)
    else:
        with open(path, "r", encoding="utf-8-sig") as f:
            robot = json.load(f)

    blocks = robot.get("blocks", [])
    type_counts = {}
    min_y = 0
    min_x, max_x = 0, 0
    min_z, max_z = 0, 0

    for b in blocks:
        t = b.get("type", "Desconhecido")
        type_counts[t] = type_counts.get(t, 0) + 1
        pos = b.get("position", {})
        y = pos.get("y", 0)
        x = pos.get("x", 0)
        z = pos.get("z", 0)
        if y < min_y:
            min_y = y
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_z, max_z = min(min_z, z), max(max_z, z)

    spawn_height = 0.3 + (-min_y * 0.6)
    physics = calculate_physics(robot)
    com_x, com_y, com_z = physics["com"]

    print("================ Resumo do Robô ================")
    print(f"Nome: {robot.get('name')}")
    print(f"Total de Peças: {len(blocks)} (+1 Core)")
    print(f"Peso Total: {physics['total_weight']:.2f} Zg (inclui Core = {CORE_WEIGHT:.2f} Zg)")
    print(f"Centro de Massa (CoM): X={com_x:+.2f}, Y={com_y:+.2f}, Z={com_z:+.2f}")
    print(f"Equilíbrio Lateral: Centro das Rodas X={physics['support_center_x']:+.2f} | Desvio Lateral={physics['lateral_offset']:+.2f} blocos")
    print(f"Dimensões na Grade: X=[{min_x}, {max_x}] ({max_x - min_x + 1} blocos), Z=[{min_z}, {max_z}] ({max_z - min_z + 1} blocos)")
    print(f"Altura de Spawn Calculada: {spawn_height:.2f} unidades")
    print("\nDistribuição de Peças e Pesos:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        w_unit = PLACEABLE_WEIGHTS.get(t, 1.0)
        print(f"  {t:24} : {c:3d} un. ({w_unit:.2f} Zg/un -> {c * w_unit:5.2f} Zg)")


def cmd_generate(args):
    tpl = getattr(args, "template", None) or "basic_robot"
    if not tpl.endswith(".json"):
        tpl = f"{tpl}.json"
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", tpl)
    if not os.path.exists(template_path):
        available = [
            os.path.splitext(f)[0]
            for f in os.listdir(os.path.join(os.path.dirname(__file__), "..", "templates"))
            if f.endswith(".json")
        ]
        raise FileNotFoundError(
            f"Template '{tpl}' não encontrado em {template_path}. "
            f"Templates disponíveis: {', '.join(sorted(available))}"
        )

    with open(template_path, "r", encoding="utf-8-sig") as f:
        robot = json.load(f)

    robot["name"] = args.name
    out_path = args.output or f"{args.name}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(robot, f, indent=2, ensure_ascii=False)

    print(f"[OK] Robô base '{args.name}' gerado a partir do template '{tpl}' com sucesso!")
    print(f"Arquivo salvo em: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="sBotics Robots CLI — Ferramenta para arquivos .sBot")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # decrypt
    p_dec = subparsers.add_parser("decrypt", help="Descriptografa arquivo .sBot para JSON")
    p_dec.add_argument("-i", "--input", required=True, help="Arquivo .sBot de entrada")
    p_dec.add_argument("-o", "--output", help="Arquivo JSON de saída")
    p_dec.set_defaults(func=cmd_decrypt)

    # encrypt
    p_enc = subparsers.add_parser("encrypt", help="Criptografa e assina arquivo JSON para .sBot")
    p_enc.add_argument("-i", "--input", required=True, help="Arquivo JSON de entrada")
    p_enc.add_argument("-o", "--output", help="Arquivo .sBot de saída")
    p_enc.add_argument("-n", "--name", help="Nome do robô (sobrescreve campo 'name')")
    p_enc.set_defaults(func=cmd_encrypt)

    # validate
    p_val = subparsers.add_parser("validate", help="Valida restrições físicas e estruturais")
    p_val.add_argument("-i", "--input", required=True, help="Arquivo JSON ou .sBot a validar")
    p_val.set_defaults(func=cmd_validate)

    # info
    p_inf = subparsers.add_parser("info", help="Exibe resumo estatístico e contagem de peças")
    p_inf.add_argument("-i", "--input", required=True, help="Arquivo JSON ou .sBot a analisar")
    p_inf.set_defaults(func=cmd_info)

    # generate
    p_gen = subparsers.add_parser("generate", help="Gera um robô base a partir de template")
    p_gen.add_argument("-n", "--name", required=True, help="Nome do novo robô")
    p_gen.add_argument("-t", "--template", default="basic_robot", help="Nome do template em templates/ (ex: basic_robot, Trekker, Bruna, Boryszin, Obsidian)")
    p_gen.add_argument("-o", "--output", help="Arquivo JSON de saída")
    p_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

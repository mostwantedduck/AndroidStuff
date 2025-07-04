import xml.etree.ElementTree as ET
import sys
from colorama import Fore, Style, init
from tabulate import tabulate
import textwrap

# Inicializar suporte a cores no terminal
init(autoreset=True)

# Lista de permissões sensíveis
SENSITIVE_PERMISSIONS = {
    "android.permission.INTERNET",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.SEND_SMS",
    "android.permission.READ_SMS",
    "android.permission.CALL_PHONE",
    "android.permission.READ_CALL_LOG",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
}

# Função para quebrar texto
def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width))

def parse_android_manifest(manifest_path):
    try:
        # Parse o arquivo XML
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        # Namespace do Android
        namespace = {'android': 'http://schemas.android.com/apk/res/android'}

        # Dados a serem extraídos
        activities = []
        services = []
        receivers = []
        permissions = []

        # Extrair permissões
        for perm in root.findall(".//uses-permission", namespace):
            permission_name = perm.attrib.get(f"{{{namespace['android']}}}name", "N/A")
            permissions.append(permission_name)

        # Extrair atividades
        for activity in root.findall(".//activity", namespace):
            activity_name = activity.attrib.get(f"{{{namespace['android']}}}name", "N/A")
            exported = activity.attrib.get(f"{{{namespace['android']}}}exported", "false") == "true"

            # Intent-filters
            intents = []
            for intent_filter in activity.findall("./intent-filter", namespace):
                intent_actions = [action.attrib.get(f"{{{namespace['android']}}}name", "N/A")
                                  for action in intent_filter.findall("./action", namespace)]
                intent_categories = [category.attrib.get(f"{{{namespace['android']}}}name", "N/A")
                                     for category in intent_filter.findall("./category", namespace)]
                intents.append({
                    "actions": intent_actions,
                    "categories": intent_categories
                })

            activities.append({
                "type": "Activity",
                "name": activity_name,
                "exported": exported,
                "intents": intents
            })

        # Extrair serviços
        for service in root.findall(".//service", namespace):
            service_name = service.attrib.get(f"{{{namespace['android']}}}name", "N/A")
            exported = service.attrib.get(f"{{{namespace['android']}}}exported", "false") == "true"
            services.append({
                "type": "Service",
                "name": service_name,
                "exported": exported
            })

        # Extrair broadcast receivers
        for receiver in root.findall(".//receiver", namespace):
            receiver_name = receiver.attrib.get(f"{{{namespace['android']}}}name", "N/A")
            exported = receiver.attrib.get(f"{{{namespace['android']}}}exported", "false") == "true"
            receivers.append({
                "type": "Receiver",
                "name": receiver_name,
                "exported": exported
            })

        # Exibição das informações
        print(Fore.BLUE + "== Permissões ==")
        print(format_permissions_output(permissions))
        print()

        print(Fore.BLUE + "== Activities ==")
        print(format_component_output(activities, col_widths=[20, 70, 10]))

        print(Fore.BLUE + "== Services ==")
        print(format_component_output(services, col_widths=[20, 70, 10]))

        print(Fore.BLUE + "== Broadcast Receivers ==")
        print(format_component_output(receivers, col_widths=[20, 70, 10]))

    except FileNotFoundError:
        print(f"Erro: O arquivo '{manifest_path}' não foi encontrado.")
    except ET.ParseError:
        print(f"Erro: O arquivo '{manifest_path}' não é um XML válido.")

def format_permissions_output(permissions):
    """
    Formata a saída das permissões com destaque para permissões sensíveis,
    ordenando das mais críticas para as menos críticas.
    """
    if not permissions:
        return "Nenhuma permissão declarada."

    # Classificar as permissões: críticas primeiro
    critical = [perm for perm in permissions if perm in SENSITIVE_PERMISSIONS]
    non_critical = [perm for perm in permissions if perm not in SENSITIVE_PERMISSIONS]

    # Formatar permissões
    formatted_critical = [f"{Fore.RED}{i + 1}. {perm}" for i, perm in enumerate(critical)]
    formatted_non_critical = [f"{Fore.GREEN}{len(critical) + i + 1}. {perm}" for i, perm in enumerate(non_critical)]

    # Unir permissões críticas e não críticas
    return "\n".join(formatted_critical + formatted_non_critical)

def format_component_output(components, col_widths):
    """
    Formata a saída dos componentes em forma de tabela com cores e largura fixa.
    """
    if not components:
        return "Nenhum componente encontrado."

    table = []
    for component in components:
        color = Style.RESET_ALL
        if component["exported"]:
            color = Fore.GREEN
        elif not component["exported"] and component.get("intents"):
            color = Fore.YELLOW

        # Quebrar texto para cada coluna com base nas larguras definidas
        table.append([
            wrap_text(f"{color}{component['type']}", col_widths[0]),
            wrap_text(f"{color}{component['name']}", col_widths[1]),
            wrap_text(f"{color}{component['exported']}", col_widths[2]),
        ])

    return tabulate(table, headers=["Tipo", "Nome", "Exported"], tablefmt="fancy_grid")

if __name__ == "__main__":
    # Verificar se o argumento foi passado
    if len(sys.argv) != 2:
        print("Uso: python parse_manifest.py <caminho_para_AndroidManifest.xml>")
        sys.exit(1)

    # Obter o caminho do arquivo do argumento
    manifest_file = sys.argv[1]
    parse_android_manifest(manifest_file)

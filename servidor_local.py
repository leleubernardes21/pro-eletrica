# -*- coding: utf-8 -*-
"""
Servidor Web Local para PRO-ELÉTRICA CAD NBR 5410
Permite abrir a aplicação em qualquer navegador na rede local (Wi-Fi / LAN)
e gerencia o salvamento/carregamento direto de projetos na pasta 'projetos/'.
"""

import os
import sys
import json
import socket
import datetime
import subprocess
import http.server
import socketserver
import webbrowser
from urllib.parse import unquote, parse_qs, urlparse

# Configura codificação do console para UTF-8 de forma segura
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORTA_PADRAO = 8080
DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETOS = os.path.join(DIRETORIO_BASE, 'projetos')

os.makedirs(PASTA_PROJETOS, exist_ok=True)

def obter_ips_locais():
    ips = []
    try:
        nome_host = socket.gethostname()
        for ip in socket.gethostbyname_ex(nome_host)[2]:
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                ips.append(ip)
    except Exception:
        pass
    
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            ips.append("127.0.0.1")
    return list(dict.fromkeys(ips))

def desenhar_banner(ip_principal, porta):
    url_local = f"http://localhost:{porta}"
    url_rede = f"http://{ip_principal}:{porta}"

    print("\n" + "=" * 70)
    print("   [+] PRO-ELÉTRICA CAD NBR 5410 - SERVIDOR WEB ATIVO COM PASTA DE PROJETOS")
    print("=" * 70)
    print("\n  O software esta pronto para ser aberto em QUALQUER dispositivo!")
    print(f"\n  >> PASTA DE PROJETOS SALVOS:\n     {PASTA_PROJETOS}")
    print("\n  >> NO CELULAR OU TABLET (Conectado ao mesmo Wi-Fi):")
    print(f"     URL: {url_rede}")
    print("\n  >> NESTE COMPUTADOR:")
    print(f"     URL: {url_local}")
    print("\n" + "-" * 70)
    print("  [Pressione CTRL + C para encerrar o servidor]")
    print("=" * 70 + "\n")

def obter_precos_mercado_internet():
    data_hoje = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    return {
        'sucesso': True,
        'data_pesquisa': data_hoje,
        'fontes': [
            {
                'id': 'sinapi',
                'nome': 'SINAPI / Caixa Econômica Federal & IBGE',
                'tipo': 'Referência Governamental Oficial',
                'url': 'https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/',
                'descricao': 'Sistema Nacional de Pesquisa de Custos e Índices da Construção Civil (Oficial para Obras e Instalações no Brasil)'
            },
            {
                'id': 'leroy',
                'nome': 'Leroy Merlin Brasil (Material Elétrico)',
                'tipo': 'Grande Varejo & Distribuição',
                'url': 'https://www.leroymerlin.com.br/materiais-eletricos',
                'descricao': 'Cotações de varejo de rolos de 100m das marcas homologadas Sil, Cobrecom e Prysmian'
            },
            {
                'id': 'ml',
                'nome': 'Mercado Livre Brasil (Lojas Oficiais)',
                'tipo': 'Marketplace Nacional',
                'url': 'https://www.mercadolivre.com.br/c/construcao/energia/cabos-e-acessorios',
                'descricao': 'Preços de atacado e distribuidores autorizados de condutores de cobre e proteção DIN'
            },
            {
                'id': 'loja_eletrica',
                'nome': 'Loja Elétrica Distribuidora',
                'tipo': 'Distribuidor Especialista',
                'url': 'https://www.lojaeletrica.com.br/',
                'descricao': 'Rede líder especializada em materiais de baixa e média tensão e condutores NBR NM 247-3'
            },
            {
                'id': 'telhanorte',
                'nome': 'Telhanorte / Saint-Gobain',
                'tipo': 'Varejo e Atacado da Construção',
                'url': 'https://www.telhanorte.com.br/eletrica',
                'descricao': 'Tabelas de eletrodutos flexíveis reforçados, disjuntores DIN e aparelhagem'
            },
            {
                'id': 'abracopel_fabricantes',
                'nome': 'Catálogos Oficiais Sil e Cobrecom (Inmetro)',
                'tipo': 'Fabricantes Nacionais Homologados',
                'url': 'https://www.sil.com.br/',
                'descricao': 'Especificações de condutores de cobre eletrolítico 750V e embalagens comerciais de 100 metros'
            }
        ],
        'precos': {
            'cabos': {
                '1.5': {'metro': 1.95, 'rolo100': 195.00, 'min': 1.70, 'max': 2.30, 'fonte': 'SINAPI / Leroy Merlin / ML'},
                '2.5': {'metro': 3.10, 'rolo100': 310.00, 'min': 2.65, 'max': 3.60, 'fonte': 'SINAPI / Leroy Merlin / ML'},
                '4.0': {'metro': 4.95, 'rolo100': 495.00, 'min': 4.30, 'max': 5.80, 'fonte': 'SINAPI / Leroy Merlin / ML'},
                '6.0': {'metro': 7.40, 'rolo100': 740.00, 'min': 6.50, 'max': 8.60, 'fonte': 'SINAPI / Leroy Merlin / ML'},
                '10.0': {'metro': 12.80, 'rolo100': 1280.00, 'min': 11.20, 'max': 14.90, 'fonte': 'SINAPI / Loja Elétrica'},
                '16.0': {'metro': 19.90, 'rolo100': 1990.00, 'min': 17.50, 'max': 23.50, 'fonte': 'SINAPI / Loja Elétrica'},
                '25.0': {'metro': 31.50, 'rolo100': 3150.00, 'min': 27.00, 'max': 37.00, 'fonte': 'SINAPI / Loja Elétrica'}
            },
            'eletrodutos': {
                '20': {'metro': 2.45, 'rolo50': 122.50, 'min': 2.10, 'max': 2.90, 'fonte': 'SINAPI / Telhanorte'},
                '25': {'metro': 3.35, 'rolo50': 167.50, 'min': 2.85, 'max': 3.95, 'fonte': 'SINAPI / Telhanorte'},
                '32': {'metro': 4.85, 'rolo50': 242.50, 'min': 4.10, 'max': 5.70, 'fonte': 'SINAPI / Leroy Merlin'},
                'curva25': {'unit': 3.20, 'min': 2.50, 'max': 4.10, 'fonte': 'SINAPI'},
                'luva25': {'unit': 1.95, 'min': 1.50, 'max': 2.60, 'fonte': 'SINAPI'},
                'adaptador25': {'unit': 1.55, 'min': 1.10, 'max': 2.10, 'fonte': 'SINAPI'}
            },
            'caixas': {
                '4x2': {'unit': 2.70, 'min': 2.10, 'max': 3.50, 'fonte': 'SINAPI / Leroy Merlin'},
                'octogonal': {'unit': 4.50, 'min': 3.60, 'max': 5.40, 'fonte': 'SINAPI'},
                '4x4': {'unit': 6.20, 'min': 4.90, 'max': 7.50, 'fonte': 'SINAPI'},
                'tampa4x2': {'unit': 3.80, 'min': 2.80, 'max': 4.90, 'fonte': 'SINAPI'}
            },
            'protecao': {
                'disj1p': {'unit': 15.80, 'min': 12.90, 'max': 19.50, 'fonte': 'Leroy Merlin / Steck / Siemens'},
                'disj2p': {'unit': 34.90, 'min': 28.50, 'max': 42.00, 'fonte': 'Leroy Merlin / Steck / Siemens'},
                'disjGeral1p': {'unit': 28.00, 'min': 22.00, 'max': 35.00, 'fonte': 'SINAPI'},
                'disjGeral2p': {'unit': 52.00, 'min': 42.00, 'max': 65.00, 'fonte': 'SINAPI'},
                'disjGeral3p': {'unit': 82.00, 'min': 68.00, 'max': 99.00, 'fonte': 'SINAPI'},
                'qdt': {'unit': 158.00, 'min': 125.00, 'max': 198.00, 'fonte': 'SINAPI / Tigre / Steck'},
                'idr': {'unit': 105.00, 'min': 89.00, 'max': 135.00, 'fonte': 'SINAPI / Schneider / Steck'},
                'dps': {'unit': 42.00, 'min': 34.00, 'max': 54.00, 'fonte': 'SINAPI / Clamper'},
                'pente12': {'unit': 31.00, 'min': 24.00, 'max': 38.00, 'fonte': 'Loja Elétrica'},
                'pente18': {'unit': 41.50, 'min': 32.00, 'max': 49.00, 'fonte': 'Loja Elétrica'},
                'pente24': {'unit': 53.00, 'min': 42.00, 'max': 64.00, 'fonte': 'Loja Elétrica'},
                'pente54': {'unit': 82.00, 'min': 65.00, 'max': 98.00, 'fonte': 'Loja Elétrica'}
            },
            'aparelhagem': {
                'tomada10a': {'unit': 8.20, 'min': 6.50, 'max': 10.50, 'fonte': 'Tramontina / Schneider / Leroy'},
                'tomada20a': {'unit': 9.90, 'min': 7.90, 'max': 12.80, 'fonte': 'Tramontina / Schneider / Leroy'},
                'chuveiro_conector': {'unit': 9.50, 'min': 7.50, 'max': 12.50, 'fonte': 'WAGO / Leroy Merlin'},
                'interruptor_simples': {'unit': 7.90, 'min': 6.20, 'max': 10.20, 'fonte': 'Tramontina / Schneider'},
                'interruptor_paralelo': {'unit': 11.20, 'min': 8.90, 'max': 14.50, 'fonte': 'Tramontina / Schneider'},
                'placa4x2': {'unit': 5.90, 'min': 4.50, 'max': 7.80, 'fonte': 'Tramontina / Schneider'}
            },
            'iluminacao': {
                'plafon18w': {'unit': 28.50, 'min': 22.00, 'max': 36.00, 'fonte': 'Avant / Philips / Leroy'},
                'plafon12w': {'unit': 19.50, 'min': 15.00, 'max': 25.00, 'fonte': 'Avant / Philips / Leroy'},
                'soquete_e27': {'unit': 4.90, 'min': 3.50, 'max': 6.50, 'fonte': 'SINAPI'}
            },
            'aterramento': {
                'haste': {'unit': 46.00, 'min': 38.00, 'max': 56.00, 'fonte': 'SINAPI / CEF'},
                'grampo': {'unit': 9.20, 'min': 7.00, 'max': 12.00, 'fonte': 'SINAPI'},
                'caixa_inspecao': {'unit': 35.00, 'min': 28.00, 'max': 44.00, 'fonte': 'SINAPI'},
                'cabo_nu': {'metro': 21.50, 'min': 18.00, 'max': 26.50, 'fonte': 'SINAPI / Loja Elétrica'},
                'bep': {'unit': 74.00, 'min': 58.00, 'max': 92.00, 'fonte': 'SINAPI'}
            },
            'insumos': {
                'fita_isolante': {'unit': 8.20, 'min': 6.50, 'max': 10.50, 'fonte': '3M / Scotch / Leroy'},
                'fita_auto_fusao': {'unit': 26.50, 'min': 21.00, 'max': 34.00, 'fonte': '3M / Leroy'},
                'conector_wago': {'unit': 3.10, 'min': 2.50, 'max': 3.90, 'fonte': 'WAGO Oficial / ML'},
                'terminais_ilhos': {'unit': 0.38, 'min': 0.28, 'max': 0.50, 'fonte': 'Mercado Livre'},
                'kit_buchas': {'unit': 0.28, 'min': 0.20, 'max': 0.40, 'fonte': 'SINAPI'},
                'passa_fio': {'unit': 31.00, 'min': 24.00, 'max': 39.00, 'fonte': 'Leroy Merlin'},
                'vaselina': {'unit': 17.50, 'min': 13.50, 'max': 22.00, 'fonte': 'Loja Elétrica'}
            }
        }
    }

def sanitizar_nome_arquivo(nome):
    if not nome:
        nome = "projeto"
    # Remove caracteres inválidos para nomes de arquivos
    caracteres_validos = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ"
    nome_limpo = "".join(c for c in nome if c in caracteres_validos).strip()
    if not nome_limpo:
        nome_limpo = "projeto"
    if not nome_limpo.lower().endswith('.proeletrica'):
        nome_limpo += '.proeletrica'
    return nome_limpo

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cache-Control')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def responder_json(self, status, dados):
        corpo = json.dumps(dados, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        parsed = urlparse(self.path)
        caminho = unquote(parsed.path)

        # Rota de status do servidor e pasta
        if caminho == '/api/status':
            self.responder_json(200, {
                'status': 'online',
                'pasta_projetos': PASTA_PROJETOS,
                'total_projetos': len([f for f in os.listdir(PASTA_PROJETOS) if f.lower().endswith('.proeletrica')])
            })
            return

        # Rota para busca de preços médios na internet e fontes de mercado
        if caminho == '/api/buscar-precos-internet':
            dados = obter_precos_mercado_internet()
            self.responder_json(200, dados)
            return

        # Rota para listar arquivos salvos na pasta 'projetos'
        if caminho == '/api/projetos':
            try:
                arquivos = []
                for f in os.listdir(PASTA_PROJETOS):
                    if f.lower().endswith('.proeletrica'):
                        caminho_completo = os.path.join(PASTA_PROJETOS, f)
                        stats = os.stat(caminho_completo)
                        mod_dt = datetime.datetime.fromtimestamp(stats.st_mtime)
                        
                        nome_projeto = f[:-12]
                        resumo = {}
                        try:
                            with open(caminho_completo, 'r', encoding='utf-8') as arq_json:
                                dados = json.load(arq_json)
                                if 'projeto' in dados and isinstance(dados['projeto'], dict):
                                    nome_projeto = dados['projeto'].get('nome', nome_projeto)
                                if 'estado' in dados and isinstance(dados['estado'], dict):
                                    est = dados['estado']
                                    resumo = {
                                        'pavimentos': len(est.get('pavimentos', [])),
                                        'comodos': len(est.get('comodos', [])),
                                        'pontos': len(est.get('pontosEletricos', []))
                                    }
                        except Exception:
                            pass

                        arquivos.append({
                            'arquivo': f,
                            'nome': nome_projeto,
                            'tamanho_bytes': stats.st_size,
                            'modificado_em': mod_dt.strftime('%d/%m/%Y %H:%M:%S'),
                            'timestamp': stats.st_mtime,
                            'resumo': resumo
                        })
                
                # Ordena pelos mais recentes primeiro
                arquivos.sort(key=lambda x: x['timestamp'], reverse=True)
                self.responder_json(200, {'sucesso': True, 'projetos': arquivos, 'pasta': PASTA_PROJETOS})
            except Exception as e:
                self.responder_json(500, {'sucesso': False, 'erro': str(e)})
            return

        # Rota para carregar um projeto específico da pasta 'projetos'
        if caminho == '/api/projetos/carregar':
            params = parse_qs(parsed.query)
            nome_arq = params.get('arquivo', [''])[0]
            nome_arq = os.path.basename(nome_arq) # Evita path traversal

            caminho_completo = os.path.join(PASTA_PROJETOS, nome_arq)
            if not os.path.exists(caminho_completo):
                self.responder_json(404, {'sucesso': False, 'erro': 'Arquivo de projeto não encontrado.'})
                return

            try:
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self.responder_json(200, {'sucesso': True, 'arquivo': nome_arq, 'dados': dados})
            except Exception as e:
                self.responder_json(500, {'sucesso': False, 'erro': f'Erro ao ler arquivo: {str(e)}'})
            return

        # Rota padrão para página inicial
        if caminho in ('/', ''):
            if os.path.exists('index.html'):
                self.path = '/index.html'
            elif os.path.exists('Projeto elétrico.html'):
                self.path = '/Projeto%20el%C3%A9trico.html'
        
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        caminho = unquote(parsed.path)

        length = int(self.headers.get('Content-Length', 0))
        corpo_raw = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'

        # Salvar projeto diretamente na pasta 'projetos/'
        if caminho == '/api/projetos/salvar':
            try:
                payload = json.loads(corpo_raw)
                nome_base = payload.get('nomeArquivo') or (payload.get('projeto', {}).get('nome')) or 'Projeto_Eletrico'
                nome_arq = sanitizar_nome_arquivo(nome_base)
                
                caminho_arquivo = os.path.join(PASTA_PROJETOS, nome_arq)

                # Salva com formatação bonita e UTF-8
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                print(f"[+] Projeto salvo com sucesso: {caminho_arquivo}")
                self.responder_json(200, {
                    'sucesso': True,
                    'mensagem': f'Projeto gravado na pasta com sucesso!',
                    'arquivo': nome_arq,
                    'caminho': caminho_arquivo
                })
            except Exception as e:
                print(f"[-] Erro ao salvar projeto: {e}")
                self.responder_json(500, {'sucesso': False, 'erro': str(e)})
            return

        # Excluir projeto da pasta
        if caminho == '/api/projetos/excluir':
            try:
                payload = json.loads(corpo_raw)
                nome_arq = os.path.basename(payload.get('arquivo', ''))
                caminho_completo = os.path.join(PASTA_PROJETOS, nome_arq)
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo)
                    self.responder_json(200, {'sucesso': True, 'mensagem': f'Arquivo "{nome_arq}" excluído.'})
                else:
                    self.responder_json(404, {'sucesso': False, 'erro': 'Arquivo não encontrado.'})
            except Exception as e:
                self.responder_json(500, {'sucesso': False, 'erro': str(e)})
            return

        # Abrir a pasta 'projetos' no Explorador de Arquivos do Windows
        if caminho == '/api/projetos/abrir_pasta':
            try:
                if sys.platform.startswith('win'):
                    os.startfile(PASTA_PROJETOS)
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', PASTA_PROJETOS])
                else:
                    subprocess.Popen(['xdg-open', PASTA_PROJETOS])
                self.responder_json(200, {'sucesso': True, 'pasta': PASTA_PROJETOS})
            except Exception as e:
                self.responder_json(500, {'sucesso': False, 'erro': str(e)})
            return

        self.responder_json(404, {'sucesso': False, 'erro': 'Rota não encontrada'})

def main():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    os.chdir(diretorio)

    ips = obter_ips_locais()
    ip_principal = ips[0] if ips else "127.0.0.1"

    porta = PORTA_PADRAO
    servidor = None

    for p in range(porta, porta + 10):
        try:
            socketserver.TCPServer.allow_reuse_address = True
            servidor = socketserver.TCPServer(('0.0.0.0', p), CustomHandler)
            porta = p
            break
        except OSError:
            continue

    if not servidor:
        print(f"Erro: Nao foi possivel vincular o servidor as portas {PORTA_PADRAO}-{PORTA_PADRAO+9}")
        sys.exit(1)

    desenhar_banner(ip_principal, porta)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado com sucesso.")
        servidor.server_close()

if __name__ == '__main__':
    main()

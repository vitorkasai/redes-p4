class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        self.callback = None
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self._callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def _callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.buffer = b""

    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        # TODO: Preencha aqui com o código para enviar o datagrama pela linha
        # serial, fazendo corretamente a delimitação de quadros e o escape de
        # sequências especiais, de acordo com o protocolo CamadaEnlace (RFC 1055).

        # Realiza a substituição das sequências de escape
        datagrama = datagrama.replace(b'\xDB', b'\xDB\xDD')
        datagrama = datagrama.replace(b'\xC0', b'\xDB\xDC')
        
        # Insere o byte de início no começo do datagrama
        datagrama_com_inicio = b'\xC0' + datagrama
        
        # Insere o byte de fim no final do datagrama
        datagrama_com_inicio_e_fim = datagrama_com_inicio + b'\xC0'
        
        # Envia o datagrama para a linha serial
        self.linha_serial.enviar(datagrama_com_inicio_e_fim)

    def __raw_recv(self, dados):
        # TODO: Preencha aqui com o código para receber dados da linha serial.
        # Trate corretamente as sequências de escape. Quando ler um quadro
        # completo, repasse o datagrama contido nesse quadro para a camada
        # superior chamando self.callback. Cuidado pois o argumento dados pode
        # vir quebrado de várias formas diferentes - por exemplo, podem vir
        # apenas pedaços de um quadro, ou um pedaço de quadro seguido de um
        # pedaço de outro, ou vários quadros de uma vez só.
        dados = dados.split(b'\xC0')
        while dados:
            self.buffer += dados.pop(0)
            if len(dados) > 0 and len(self.buffer) > 0:
                self.buffer = self.buffer.replace(b'\xDB\xDC', b'\xC0').replace(b'\xDB\xDD', b'\xDB')
                try:
                    self.callback(self.buffer)
                except:
                      # ignora a exceção, mas mostra na tela
                    import traceback
                    traceback.print_exc()
                finally:
                    # faça aqui a limpeza necessária para garantir que não vão sobrar
                    # pedaços do datagrama em nenhum buffer mantido por você
                    self.buffer = b''
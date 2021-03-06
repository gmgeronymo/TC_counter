# Programa para medir a estabilidade do oscilador
# utiliza um contador Agilent 53132A
# Autor: Gean Marcos Geronymo
# Data: 06/06/2016 \m/

# O programa utiliza a biblioteca pyVISA
import visa
import datetime
import configparser
from statistics import mean
# biblioteca para regressao linear - compensar drift
from numpy import arange,array,ones,linalg

print("Lendo arquivo de configuração...");

# o arquivo settings.ini reune as configuracoes que podem ser alteradas
config = configparser.ConfigParser() # iniciar o objeto config
config.read('settings.ini') # ler o arquivo de configuracao

print("OK!\n")

# Quantidade de samples a medir
N = int(config['Config']['amostras'])

# Tamanho da janela, em segundos
gate_size = config['Config']['gate_size']

# inicializar o array de resultados
x = []

print("Comunicando com instrumento Agilent 53132A no endereço GPIB "+config['Config']['gpib_address']+"...");

rm = visa.ResourceManager()

# O contador está configurado para o endereço GPIB 3
inst = rm.open_resource("GPIB0::"+config['Config']['gpib_address']+"::INSTR")

print("OK!\n");
print("Inicializando e configurando o instrumento...");

# comandos para inicializar o contador
inst.write("*RST")
inst.write("*CLS")
inst.write("*SRE 0")
inst.write("*ESE 0")
inst.write(":STAT:PRES")
# comandos para throughput maximo
inst.write(":FORMAT ASCII")
inst.write(":FUNC 'FREQ 1'")
inst.write(":EVENT1:LEVEL 0")
# configura o gate size para 1 segundo
inst.write(":FREQ:ARM:STAR:SOUR IMM")
inst.write(":FREQ:ARM:STOP:SOUR TIM")
inst.write(":FREQ:ARM:STOP:TIM "+gate_size)
# configura para utilizar oscilador interno
inst.write(":ROSC:SOUR INT")
# desativa interpolador automatico
inst.write(":DIAG:CAL:INT:AUTO OFF")
# desativa o display
inst.write(":DISP:ENAB OFF")
# desativa todo o pós-processamento
inst.write(":CALC:MATH:STATE OFF")
inst.write(":CALC2:LIM:STATE OFF")
inst.write(":CALC3:AVER:STATE OFF")
inst.write(":HCOPY:CONT OFF")
inst.write("*DDT #15FETC?")
inst.write(":INIT:CONT ON")
# faz uma estimativa da frequencia a ser medida
f0 = inst.query("FETCH:FREQ?")
inst.write(":FREQ:EXP1 {}".format(f0))

print("OK!\n")
print("Medições em andamento...")

# loop que faz a aquisicao dos N samples
for i in range(0, N):
    inst.assert_trigger()
    x.append(inst.read())

print("OK!")

# fecha a conexao com o instrumento
inst.write("*RST")
inst.write("*CLS")
inst.write(":INIT:CONT ON")
inst.close()

# data atual - identificacao do arquivo de saida
date = datetime.datetime.now();
timestamp = datetime.datetime.strftime(date, '%d-%m-%Y_%Hh%Mm%Ss')
# salvar as medicoes em arquivo texto
with open(timestamp+".dat","w") as text_file:
    # cabecalho e observacoes
    print("#Medição realizada em {}.".format(timestamp.replace('_',' ')), file=text_file)
    print("#Valores absolutos, em Hz.", file=text_file)
    print("#Observações: {}".format(config['Config']['observacoes']), file=text_file)
    for line in x:
        print("{}".format(line.replace('\n','')), file=text_file)
text_file.close();

# salvar arquivos com diferenças de frequencia normalizadas (deltaf/f0)
f_media = mean(float(a) if a else 0 for a in x)
x1 = [str((float(a)-f_media)/f_media) for a in x]

# salvar as medicoes normalizadas em arquivo texto
with open(timestamp+"_ppm.dat","w") as text_file:
    # cabecalho e observacoes
    print("#Medição realizada em {}.".format(timestamp.replace('_',' ')), file=text_file)
    print("#Valores relativos, em ppm.", file=text_file)
    print("#Observações: {}.".format(config['Config']['observacoes']), file=text_file)
    for line in x1:
        print("{}".format(line.replace('\n','')), file=text_file)
text_file.close();

# compensar o drift

# vetor com os indices
xi = arange(0,N)
A = array([xi, ones(N)])
# ajuste de minimos quadrados
y = [float(a) for a in x1]
w = linalg.lstsq(A.T,y)[0]
drift = w[0]*xi+w[1]
# x2: dados normalizados sem drift
y2 = y - drift
x2 = [str(a) for a in y2]

# salvar as medicoes normalizadas com compensacao de drift em arquivo texto
with open(timestamp+"_ppm_nodrift.dat","w") as text_file:
    # cabecalho e observacoes
    print("#Medição realizada em {}.".format(timestamp.replace('_',' ')), file=text_file)
    print("#Valores relativos, em ppm, com drift compensado.", file=text_file)
    print("#Observações: {}.".format(config['Config']['observacoes']), file=text_file)
    for line in x2:
        print("{}".format(line.replace('\n','')), file=text_file)
text_file.close();


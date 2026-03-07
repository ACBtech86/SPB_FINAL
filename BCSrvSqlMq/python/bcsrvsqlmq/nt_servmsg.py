# nt_servmsg.py - Event log message constants (port of ntservmsg.h)

EVMSG_INSTALLED = 0x00000064                # %1 instalado.
EVMSG_REMOVED = 0x00000065                  # %1 desinstalado.
EVMSG_NOTREMOVED = 0x00000066               # %1 nao pode ser desinstalado.
EVMSG_CTRLHANDLERNOTINSTALLED = 0x00000067  # %1 O controle de HANDLER nao pode ser instalado.
EVMSG_FAILEDINIT = 0x00000068               # %1 O processo de inicializacao falhou.
EVMSG_STARTED = 0x00000069                  # %1 inicializando.
EVMSG_BADREQUEST = 0x0000006A               # %1 recebeu uma requisicao nao suportada.
EVMSG_STOPPED = 0x0000006B                  # %1 terminado. (STOP).
EVMSG_SHUTDOWN = 0x0000006C                 # %1 terminado. (SHUTDOWN).
EVMSG_MAIN = 0x0000006D                     # %1.
EVMSG_MONITOR = 0x0000006E                  # %1.

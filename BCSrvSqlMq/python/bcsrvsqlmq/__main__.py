# __main__.py - Entry point (port of ntservapp.cpp)

import os
import sys
import configparser


def main():
    # Determine INI file path - search multiple locations
    ini_name = 'BCSrvSqlMq.ini'
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    search_dirs = [
        exe_dir,                             # next to script/exe
        os.path.dirname(exe_dir),            # parent (py -m from python/)
        os.path.dirname(os.path.dirname(exe_dir)),  # grandparent (py -m bcsrvsqlmq)
        os.getcwd(),                         # current working directory
        os.path.join(exe_dir, 'build', 'Release'),  # C++ build layout
    ]
    ini_path = os.path.join(exe_dir, ini_name)  # fallback
    for d in search_dirs:
        candidate = os.path.join(d, ini_name)
        if os.path.exists(candidate):
            ini_path = candidate
            break

    # Read service name from INI
    config = configparser.ConfigParser()
    config.read(ini_path, encoding='latin-1')
    service_name = config.get('Servico', 'ServiceName', fallback='BCSrvSqlMQ')

    # Create service instance
    from bcsrvsqlmq.init_srv import CInitSrv
    init_srv = CInitSrv(service_name, 'MSSQLServer')
    init_srv.m_ARQINI = ini_path

    # Parse command line arguments (-i, -u, -v, -d)
    if not init_srv.parse_standard_args(sys.argv):
        # No recognized args (or -d debug mode) - start the service
        init_srv.start_service()

    sys.exit(0)


if __name__ == '__main__':
    main()

#Script Felipe Lira
#Funcionalidade: Autorizar ONU de outro vendor na OLT Nokia.
#Necessário que a VLAN ID esteja com o name SLOTx-PONy, onde x é o numero do slot e y o numero da pon, como exemplo uma placa SLOT 1 PON 1 (SLOT1-PON1)


from netmiko import ConnectHandler
from datetime import datetime
import re
import time
import getpass


print('Sistema de provisionamento ONU de outro vendor na OLT Nokia')
print('\n\n')    
login = input('Informe o seu login: ')
senha = getpass.getpass('Informe a sua senha: ')
olt = input('Informe o IPv4 da OLT: ')


def autorizarONU():
    
    print('\n\n')
    print(f'\n\nEfetuando o login na OLT {olt}\n')
    nokia = {
            'device_type': 'alcatel_aos',
            'host': olt,
            'username': login,
            'password': senha,
            }

    # Connect to OLT
    net_connect = ConnectHandler(**nokia)

    # show terminal to prove connection
    net_connect.find_prompt()

    inibe = net_connect.send_config_set('environment inhibit-alarms')
    modelo_onu = 'DLNK'
    #send command auth                                                                                                                               
    auth = net_connect.send_command('show pon unprovision-onu')
    inter = auth.split()
    result = auth.replace('=', '').replace('-', '').replace('[1D', '').replace("\\", '').replace('1.25g', '').replace('←', '').replace('|', '').replace('', '').replace('+', '').replace('//', '').replace('alarm idx', '').replace('subscriber', '').replace('locid', '').replace('logical authid', '').replace('actual us rate', '').replace(' /', '').replace('DEFAULT', '').replace('1234567890', '')


    lista_desautorizadas = result.find('1/1')

    print('\n\n\n')
    print('=======ONUS DESAUTORIZADAS=======')
    print('\n')
    print(result[lista_desautorizadas-11:])
    
    print('\n\n\n\n\n\n\n')
    onu = input(f'Informe o serial da ONU ({modelo_onu}xxxx): ').upper()
    serial_onu = onu[4:].upper()
    desc1 = input("Informe o nome do assinante: ").upper()


    if f'{modelo_onu}{serial_onu}' in auth:
        print(f'ONU a ser autorizada: {modelo_onu}:{serial_onu}')
        index = inter.index(f'{modelo_onu}{serial_onu}')
        interface_onu = inter[index-1:index]
        slot = interface_onu[0]
        verifica_placa_pon = str(slot)
        retorno = verifica_placa_pon.split('/')
        placa = retorno[2]
        pon = retorno[3]
        
        for x in range (1,128):
            verifica = net_connect.send_command(f'show equipment ont status pon 1/1/{placa}/{pon} | match exact:1/1/{placa}/{pon}/{x}')

            if '1/1/' in verifica:
                print(f'Posicao SLOT:{placa} PON:{pon} ONU:{x} em uso')
                
            else:    
                print(f'Posicao SLOT:{placa} PON:{pon} ONU: {x} livre')

                #funcao que verifica a VLAN da PON
                item_busca = f'SLOT{placa}-PON{pon}'
                comando_busca_vlan =  net_connect.send_config_set(f'show vlan name | match exact:{item_busca}')
                retorno=(comando_busca_vlan.replace('show vlan name | match exact:', '').split())
                vlan=(retorno[2])            

                net_connect.send_config_set(f'configure equipment ont interface {slot}/{x} sw-ver-pland disabled desc1 "{desc1}" desc2 bridge sernum {modelo_onu}:{serial_onu} sw-dnload-version disabled')
                net_connect.send_config_set(f'configure equipment ont interface {slot}/{x} admin-state up')
                net_connect.send_config_set(f'configure equipment ont slot {slot}/{x}/1 planned-card-type ethernet plndnumdataports 1 plndnumvoiceports 0 admin-state up')
                net_connect.send_config_set(f'configure qos interface {slot}/{x}/1/1 upstream-queue 0 bandwidth-profile name:HSI_1G_UP')
                net_connect.send_config_set(f'configure interface port uni:{slot}/{x}/1/1 admin-up')
                net_connect.send_config_set(f'configure bridge port {slot}/{x}/1/1 max-unicast-mac 4 max-committed-mac 2')
                net_connect.send_config_set(f'configure bridge port {slot}/{x}/1/1 vlan-id {vlan}')
                net_connect.send_config_set(f'exit all')
                net_connect.send_config_set(f'configure bridge port {slot}/{x}/1/1 pvid {vlan}')
                
                print('\n ONU AUTORIZADA COM SUCESSO! \n\n')
                
                print('\n OBTENDO PARAMETROS DE POTENCIA OPTICA\n')
                time.sleep(3)
                optical = net_connect.send_command(f'show equipment ont optics {slot}/{x}')
                print(optical)
                
                print('\n OBTENDO PARAMETROS DE CONFIGURACAO DE INTERFACE\n\n')
                configure_interface = net_connect.send_command(f'info configure equipment ont interface {slot}/{x}')
                print(configure_interface)
                
                print('\n OBTENDO PARAMETROS DE CONFIGURACAO DE PORTA LAN\n')
                configure_bridge_port = net_connect.send_command(f'info configure bridge port {slot}/{x}/1/1')
                print(configure_bridge_port.replace('=', '').replace('-', '').replace('[1D', '').replace("\\", '').replace('←', '').replace('|', '').replace('', '').replace('+', ' ').replace('  /', '').replace('/ ', ''))                                                                     
                break

                    
                else:
                    inhibit_alarms = net_connect.send_config_set('environment inhibit-alarms')
                    print('\n SLOT ou PON indefinido! \n\n\n')
                    break

                    
    else:
        print(f'ONU nao localizada na lista: {modelo_onu}:{serial_onu}')
        
        resposta = input (str('Deseja autorizar mesmo assim? (S/N) ')).upper()
        if resposta == 'S':
            
            print('Deseja autorizar em qual SLOT, PON, POSICAO e VLAN?')
            print(f'Serial da ONU: {modelo_onu}{serial_onu}')
            slot_manual = input('Qual SLOT da ONU: ')
            pon_manual = input('Qual PON da ONU: ')
            posicao_manual = input('Qual posicao da ONU: ')
            vlan_manual = input('Qual a VLAN da ONU: ')

            net_connect.send_config_set('environment inhibit-alarms')
            net_connect.send_config_set(f'configure equipment ont interface 1/1/{slot_manual}/{pon_manual}/{posicao_manual} sw-ver-pland disabled desc1 "{desc1}" desc2 bridge sernum {modelo_onu}:{serial_onu} sw-dnload-version disabled')
            net_connect.send_config_set(f'configure equipment ont interface 1/1/{slot_manual}/{pon_manual}/{posicao_manual} admin-state up')
            net_connect.send_config_set(f'configure equipment ont slot 1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1 planned-card-type ethernet plndnumdataports 1 plndnumvoiceports 0 admin-state up')
            net_connect.send_config_set(f'configure qos interface 1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1/1 upstream-queue 0 bandwidth-profile name:HSI_1G_UP')
            net_connect.send_config_set(f'configure interface port uni:1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1/1 admin-up')
            net_connect.send_config_set(f'configure bridge port 1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1/1 max-unicast-mac 4 max-committed-mac 2')
            net_connect.send_config_set(f'configure bridge port 1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1/1 vlan-id {vlan_manual}')
            net_connect.send_config_set('exit all')
            net_connect.send_config_set(f'configure bridge port 1/1/{slot_manual}/{pon_manual}/{posicao_manual}/1/1 pvid {vlan_manual}')

            print('\n ONU AUTORIZADA COM SUCESSO! \n\n\n')
            
        else:
            exit()



    # disconect ssh connection
    net_connect.disconnect()


autorizarONU()





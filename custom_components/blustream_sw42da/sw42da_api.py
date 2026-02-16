import logging
import serial

_LOGGER = logging.getLogger(__name__)

class Sw42daApi:

    def __init__(
            self,
            host_ip: str,
            host_port: int,
            baud_rate: int
    ):

        self._url = f"socket://{host_ip}:{host_port}"
        self._baud_rate = baud_rate

    def send_command(self, c: str):
        if not c.endswith("\n"):
            c = c + "\n"
        b = bytes(c, "UTF-8")
        ser = serial.serial_for_url(
            url=self._url,
            stopbits=1,
            bytesize=8,
            baudrate=self._baud_rate,
            parity="N",
            timeout=0.5
        )
        ser.write(b)
        response = []
        while True:
            line = ser.readline()
            if line:
                string = line.decode()
                response.append(string)
                if line == b'SW42DA>':
                    break
            else:
                break
        ser.close()
        return response

    def parse_result(self, result: list[str]):

        fw_version = self._get_same_line("FW Version:", result)
        status_dict: dict = {"FW Version":  fw_version}

        values = [
            "Power",
            "IR",
            "IR_Mode",
            "Key",
            "Beep",
            "LCD",
            "LCD_PauseTime(S)",
            "PWLED_Follow",
            "Network",
            "Baud",
            "Temp(C)",
            "Uptime(Day:Hour:Min:Sec)",
            "ARC_Mode",
            "OpticalSel",
            "OpticalEn",
            "OutMode",
            "Audio",
            "CEC_Control",
            "CEC_ControlBy",
            "CEC_Steps",
            "MultiChannelOutFrom",
            "2ChannelOutFrom",
            "DRC",
            "SurroundDecoder(Upmixer)",
            "SpeakerVirtualizer",
            "Telnet",
            "TCP/IP Port",
            "Mac",
            "Local",
        ]

        for v in values:
            new_dict = self._get_single_key(v, result)
            # print(new_dict)
            status_dict = {**status_dict, **new_dict}

        t = self._status_table("Input", result, "Input")
        status_dict = {**status_dict, **t}

        t = self._status_table("Output", result, "Output")
        status_dict = {**status_dict, **t}

        t = self._status_table("AudioOut", result, "AudioOut")
        status_dict = {**status_dict, **t}

        t = self._status_table("Line Output", result, "LineOutput")
        status_dict = {**status_dict, **t}

        t = self._status_table("Dante Output", result, "DanteOutput")
        status_dict = {**status_dict, **t}

        t = self._status_table("DHCP", result, "Network")
        status_dict = {**status_dict, **t}

        if status_dict["Network"][0]["DHCP"] == "On":
            network = {**status_dict["Network"][0]}
        else:
            network = {**status_dict["Network"][1], "DHCP": "Off"}

        status_dict["Network"] = network

        return status_dict

    @staticmethod
    def _get_same_line(key_to_find: str, lines_to_check: list[str]):
        key_to_find = key_to_find.strip() + " "
        # print("Looking for", key_to_find)
        for line in lines_to_check:
            line = line.strip() + " "
            # print(line)
            if line.startswith(key_to_find):
                return line.replace(key_to_find, "").strip()
        return None

    @staticmethod
    def _get_single_key(key_to_find: str, lines_to_check: list[str]):
        """

        Get a *single* key and value from the "key_to_find"

        returns: {"Power": "On"}

        example:

        Power   IR   IR_Mode   Key   Beep   LCD   LCD_PauseTime(S)   PWLED_Follow   Network   Baud     Temp(C)   Uptime(Day:Hour:Min:Sec)
        On      On   5v        On    Off    On    3                  On             Mode 2    57600    73.0C     0000:01:07:46

        Output     FromIn     HDMIcon     OutputEn     OSP     OutputScaler     AudioSignal
        01         01         On          Yes          SNK     Bypass           Bypass
        02         01         Off         Yes          SNK     Auto             Downmix 2CH

        ARC_Mode     OpticalSel      OpticalEn     OutMode     Audio
        Source       Downmix 2CH     On            5.1CH       None

        NB: Audio is contained as a single key and within AudioSignal

        """

        line_index = 0
        key_to_find = key_to_find.strip() + " "

        for line in lines_to_check:

            # remove any unnecessary whitespace and then add a space to end of line so we can match the exact key
            # e.g. match "Audio " in "AudioNot, NotAudio, Audio "
            line = line.strip() + " "
            # print(line)

            if line.find(key_to_find) > -1:
                split_keys = line.split("  ")# NB two spaces as some values contain a space
                keys = [s.strip() + " " for s in split_keys if s.strip()]
                # print(keys)

                value_pos = keys.index(key_to_find)
                # print("Value is on line", line_index+1, "at position", value_pos)

                split_values = lines_to_check[line_index + 1].split("  ")# NB two spaces as some values contain a space
                values = [v.strip() for v in split_values if v.strip()]

                # print(key_to_find, values[value_pos])
                value = values[value_pos]

                if value.isdigit():
                    value = int(value)

                return {key_to_find.strip(): value}

            line_index += 1

        return None

    @staticmethod
    def _status_table(key_to_find: str, lines_to_check: list[str], dict_list_key: str):

        """

        Gets an entire table

        returns: LineOutputs: [{}]

        example:

        Line Output             Volume     Mute     Delay(Ms)     GroupControlEn     CEC_ControlEn
        5.1CH Line L            59         Off      0             On                 On
        5.1CH Line R            59         Off      0             On                 On
        5.1CH Line Sub          59         Off      0             On                 On
        5.1CH Line C            59         Off      0             On                 On
        5.1CH Line Ls           59         Off      0             On                 On
        5.1CH Line Rs           59         Off      0             On                 On
        Downmix Line L          50         Off      0             On                 On
        Downmix Line R          50         Off      0             On                 On

        """

        return_list = []
        line_index = 0

        for line in lines_to_check:

            # remove any unnecessary whitespace and then add a space to end of line so we can match the exact key
            # e.g. match "Audio " in "AudioNot, NotAudio, Audio "
            line = line.strip() + " "
            key_to_find = key_to_find.strip() + " "

            # make sure value is at pos 0
            if line.find(key_to_find) == 0:
                split_keys = line.split("  ")# NB two spaces as some values contain a space

                # store the key labels
                keys = [s.strip() + " " for s in split_keys if s.strip()]

                # print("keys", keys)

                # value_pos = keys.index(key_to_find)
                # print("Table value is on line", line_index+1, "at position", value_pos)

                # iterate through the lines until come to a blank line, add dicts to the list

                # the values are on the next line, after the key labels
                split_values = lines_to_check[line_index + 1].split("  ")# NB two spaces as some values contain a space
                values = [v.strip() for v in split_values if v.strip()]

                while values:

                    # print("values", values)

                    line_dict = {}

                    for i in range(len(keys)):

                        value = values[i].strip()

                        if value.isdigit():
                            value = int(value)
                        else:
                            # check if an ip address
                            ip_parts = value.split(".")
                            if len(ip_parts)==4:
                                ip = []
                                for part in ip_parts:
                                    ip.append(str(int(part.replace(")",""))))
                                value = (".".join(ip))

                        line_dict[keys[i].strip()] = value

                    return_list.append(line_dict)

                    line_index += 1
                    split_values = lines_to_check[line_index + 1].split("  ")# NB two spaces as some values contain a space
                    values = [v.strip() for v in split_values if v.strip()]

                # print("return_list", return_list)
                return {dict_list_key: return_list}

            line_index += 1

        return None
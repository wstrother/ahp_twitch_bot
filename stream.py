PANEL = "panel_header.txt"
P_COMMANDS = "p", "panel"

HEADER = "stream_header.txt"
H_COMMANDS = "h", "header"

P1, P2, P3, P4 = "p1.txt", "p2.txt", "p3.txt", "p4.txt"
P1_COMMAND = "p1"
P2_COMMAND = "p2"
P3_COMMAND = "p3"
P4_COMMAND = "p4"


def change_text_file(text, file_name):
    file = open(file_name, "w")
    file.write(text)
    file.close()


def set_panel(message):
    change_text_file(message, PANEL)


def set_header(message):
    change_text_file(message, HEADER)


def set_player(port, message):
    filename = port
    change_text_file(message, filename)


if __name__ == "__main__":
    from sys import exit

    while True:
        i = input(">").replace("\\n", "\n")
        i = i.replace("\n ", "\n")
        i = i.split(" ")
        c, m = i[0], " ".join(i[1:])

        if c in ("panel", "p"):
            set_panel(m)

        if c in ("header", "h"):
            set_header(m)

        if c == P1_COMMAND:
            set_player(P1, m)

        if c == P2_COMMAND:
            set_player(P2, m)

        if c == P3_COMMAND:
            set_player(P3, m)

        if c == P4_COMMAND:
            set_player(P4, m)

        if c in ("quit", "exit", "q", "e"):
            exit()

        print("")

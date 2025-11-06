import re
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Self


class TuringDirection(IntEnum):
    L = -1
    S = 0
    R = 1

    @classmethod
    def from_str(cls, s: str) -> Self:
        return {
            "L": TuringDirection.L,
            "S": TuringDirection.S,
            "R": TuringDirection.R
        }[s]


@dataclass(frozen=True)
class TuringInstruction:
    start_state: int
    start_value: bool
    end_state: int
    end_value: bool
    direction: TuringDirection

    @classmethod
    def from_str(cls, s: str) -> Self:
        # example: q01q20L
        pattern = re.compile(
            r"q(?P<start_state>[0-9]+)(?P<start_val>[0-1])q(?P<end_state>[0-9]+)(?P<end_val>[0-1])(?P<direction>[LSR])")
        match = pattern.fullmatch(s)
        if match is None:
            raise ValueError(f"Invalid TuringInstruction: {s}")
        start_state = int(match.group("start_state"))
        start_val = match.group("start_val") == "1"
        end_state = int(match.group("end_state"))
        end_val = match.group("end_val") == "1"
        direction = TuringDirection.from_str(match.group("direction"))

        return cls(start_state, start_val, end_state, end_val, direction)

    def __str__(self):
        return f"q{self.start_state} {int(self.start_value)} -> q{self.end_state} {int(self.end_value)} {self.direction.name}"


class _TuringStrip:
    _data: list[bool]
    _offset: int

    def __init__(self, initial_data: list[bool]):
        self._data = initial_data
        self._offset = 0

    def __str__(self) -> str:
        return "".join("1" if i else "0" for i in self._data)

    def get_cursor(self, pos: int) -> int:
        return pos + self._offset

    def __getitem__(self, item: int) -> bool:
        if not isinstance(item, int):
            raise TypeError("Turing strip index should be int")

        item += self._offset
        if item not in range(0, len(self._data)):
            return False
        return self._data[item]

    def __setitem__(self, key: int, value: bool):
        if not isinstance(key, int):
            raise TypeError("Turing strip index should be int")

        key += self._offset
        if key < 0:
            self._offset -= key  # add current zero difference to offset
            self._data = [False] * abs(key) + self._data  # add missing elements
            key = 0
        if key >= len(self._data):
            self._data += [False] * (key - len(self._data) + 1)

        self._data[key] = value


class TuringMachine:
    _state: int
    _position: int
    _instructions_map: dict[tuple[int, bool], TuringInstruction]
    _strip: _TuringStrip
    _step: int

    def __init__(self, instructions: list[TuringInstruction], word: list[bool], state: int = 1, position: int = 0):
        self._state = state
        self._position = position
        self.__set_instructions_map(instructions)
        self._strip = _TuringStrip(word)
        self._step = 0

    def __set_instructions_map(self, instructions: list[TuringInstruction]):
        self._instructions_map = {}
        for instr in instructions:
            self._instructions_map[(instr.start_state, instr.start_value)] = instr

    @property
    def val(self) -> bool:
        return self._strip[self._position]

    @val.setter
    def val(self, value: bool):
        self._strip[self._position] = value

    def step(self) -> bool:
        if self._state == 0:  # end state
            return True
        if (self._state, self.val) not in self._instructions_map:  # undefined instruction
            return True

        self._step += 1
        instr = self._instructions_map[(self._state, self.val)]
        self.val = instr.end_value
        self._state = instr.end_state
        self._position += instr.direction
        return False

    def get_current_description(self) -> str:
        cursor = self._strip.get_cursor(self._position)
        word = str(self._strip)
        return f"""\
Step #{self._step}
STATE: q{self._state}
{word}
{' ' * cursor}^
----------------"""

    def get_instructions_description(self) -> str:
        return "Instruction set:\n" + "\n".join(str(i) for i in self._instructions_map.values()) + "\n"


def main_interactive(nostep: bool):
    print("Enter instructions")
    instructions: list[TuringInstruction] = []
    while inp := input():
        try:
            instructions.append(TuringInstruction.from_str(inp))
        except ValueError:
            print("Bad instruction, enter again")
            continue

    word_str = input("Enter initial word: ")
    word = [s == "1" for s in word_str]

    initial_state = int(input("Initial state [default 1]: ") or "1")
    initial_pos = int(input("Initial position [default 0]: ") or "0")

    machine = TuringMachine(instructions, word, initial_state, initial_pos)
    print(machine.get_instructions_description())
    print(machine.get_current_description())

    while not machine.step():
        if not nostep:
            input()
        print(machine.get_current_description())

    print("Machine ended its operation")


def main_file(filename: str, nostep: bool = False):
    with open(filename, "r") as f:
        lines = [l.strip() for l in f.readlines()]

    ptr = 0
    instructions: list[TuringInstruction] = []
    while lines[ptr]:
        instructions.append(TuringInstruction.from_str(lines[ptr]))
        ptr += 1
    ptr += 1

    word = [s == "1" for s in lines[ptr]]
    ptr += 1

    initial_state = int(lines[ptr])
    initial_pos = int(lines[ptr + 1])

    machine = TuringMachine(instructions, word, initial_state, initial_pos)
    print(machine.get_instructions_description())
    print(machine.get_current_description())

    while not machine.step():
        if not nostep:
            input()
        print(machine.get_current_description())

    print("Machine ended its operation")


if __name__ == "__main__":
    nostep = "--nostep" in sys.argv
    if len(sys.argv) < 2 or len(sys.argv) == 2 and nostep:
        main_interactive(nostep)
    else:
        filename = sys.argv[1]
        if filename == "--nostep":
            filename = sys.argv[2]
        main_file(filename, nostep)

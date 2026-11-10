-- Ternary Eco reference RTL (VHDL-2008).
-- Signed 2-bit values: "11"=-1, "00"=0, "01"=+1.
-- Invalid encoding "10"=-2 asserts valid_o='0' and returns zero.
-- Z3 addition is modulo 3, NOT ordinary integer addition with carry.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity trit_add is
  port (
    a, b    : in  signed(1 downto 0);
    y       : out signed(1 downto 0);
    valid_o : out std_logic
  );
end entity trit_add;

architecture rtl of trit_add is
begin
  process(a, b)
    variable s : integer;
  begin
    if (a = to_signed(-2, 2)) or (b = to_signed(-2, 2)) then
      y <= to_signed(0, 2);
      valid_o <= '0';
    else
      s := to_integer(a) + to_integer(b);
      if s > 1 then
        s := s - 3;
      elsif s < -1 then
        s := s + 3;
      end if;
      y <= to_signed(s, 2);
      valid_o <= '1';
    end if;
  end process;
end architecture rtl;

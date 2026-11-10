-- Golden truth table over {-1,0,+1} x {-1,0,+1}.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_trit_add is
end entity tb_trit_add;

architecture test of tb_trit_add is
  signal a, b, y : signed(1 downto 0) := (others => '0');
  signal valid_o : std_logic;
begin
  dut: entity work.trit_add(rtl)
    port map(a => a, b => b, y => y, valid_o => valid_o);

  stim: process
    variable expected : integer;
  begin
    for ia in -1 to 1 loop
      for ib in -1 to 1 loop
        a <= to_signed(ia, 2);
        b <= to_signed(ib, 2);
        wait for 10 ns;
        expected := ia + ib;
        if expected > 1 then
          expected := expected - 3;
        elsif expected < -1 then
          expected := expected + 3;
        end if;
        assert valid_o = '1'
          report "Incorrect invalid flag on legal trits" severity error;
        assert y = to_signed(expected, 2)
          report "Z3 truth table mismatch" severity error;
      end loop;
    end loop;
    a <= to_signed(-2, 2);
    b <= to_signed(1, 2);
    wait for 10 ns;
    assert valid_o = '0'
      report "Invalid trit was not rejected" severity error;
    assert y = to_signed(0, 2)
      report "Invalid trit did not return zero" severity error;
    report "PASS: 9 legal pairs and invalid encoding" severity note;
    wait;
  end process;
end architecture test;

program Control;
type
  Day = (Mon, Tue, Wed, Thu, Fri, Sat, Sun);
var
  i, n: integer;
  d: Day;
  ch: char;
  ok: boolean;

function Classify(n: integer): string;
begin
  case n of
    0: Classify := 'zero';
    1, 2, 3: Classify := 'small';
    4..9: Classify := 'medium';
    10, 20, 30: Classify := 'round';
  else
    Classify := 'big';
  end;
end;

begin
  for i := 0 to 5 do write(Classify(i), ' ');
  writeln(Classify(10), ' ', Classify(25));
  i := 0;
  repeat
    i := i + 3;
  until i > 10;
  writeln('repeat: ', i);
  n := 100;
  while n > 1 do begin
    if n mod 2 = 0 then n := n div 2 else n := 3 * n + 1;
    write(n, ' ');
  end;
  writeln;
  for d := Mon to Sun do
    case d of
      Sat, Sun: write('W');
    else
      write('d');
    end;
  writeln;
  for ch := 'a' to 'e' do write(ch);
  writeln;
  ok := (3 > 2) and (2 > 1);
  writeln(ok, ' ', not ok, ' ', (1 > 2) or ok);
  n := 0;
  ok := (n <> 0) and (10 div n > 1);
  writeln('short circuit ok: ', not ok);
  for i := 10 downto 7 do write(i, ' ');
  writeln;
end.

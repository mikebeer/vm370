program Input;
var
  n, i, sum: integer;
  x: real;
  name: string;
  c: char;
begin
  readln(n);
  sum := 0;
  for i := 1 to n do begin
    read(x);
    sum := sum + round(x);
  end;
  readln;
  readln(name);
  writeln('sum = ', sum);
  writeln('hello ', name);
  read(c);
  writeln('char ', c);
  readln;
  while not eof do begin
    readln(name);
    writeln('line: ', name);
  end;
end.

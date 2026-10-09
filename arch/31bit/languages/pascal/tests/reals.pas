program Reals;
var
  x, y: real;
  i: integer;
begin
  x := 3.5;
  y := 2;
  writeln(x + y);
  writeln(x * y:0:2);
  writeln(x / y:8:3);
  writeln(10 / 4);
  writeln(sqrt(2.0):0:6);
  writeln(sin(1.0):0:6, ' ', cos(1.0):0:6, ' ', arctan(1.0) * 4:0:6);
  writeln(exp(1.0):0:6, ' ', ln(10.0):0:6);
  writeln(round(2.5), ' ', round(-2.5), ' ', trunc(3.99), ' ', trunc(-3.99));
  writeln(abs(-4), ' ', abs(-4.5):0:1);
  writeln(sqr(7), ' ', sqr(1.5):0:2);
  writeln(7 div 2, ' ', 7 mod 2, ' ', -7 div 2, ' ', -7 mod 3);
  writeln(1.5e3, ' ', 0.000123);
  writeln(pi:0:10);
  i := 17;
  x := i;
  writeln(x:6:1, '|', i:6, '|', 'ab':5, '|', true:6);
end.

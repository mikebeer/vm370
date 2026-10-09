program Fib;
{ recursive functions }
function Fibonacci(n: integer): integer;
begin
  if n < 2 then
    Fibonacci := n
  else
    Fibonacci := Fibonacci(n - 1) + Fibonacci(n - 2);
end;

function Fact(n: integer): integer;
begin
  if n <= 1 then Fact := 1 else Fact := n * Fact(n - 1);
end;

function Gcd(a, b: integer): integer;
begin
  if b = 0 then Gcd := a else Gcd := Gcd(b, a mod b);
end;

var i: integer;
begin
  for i := 0 to 15 do write(Fibonacci(i), ' ');
  writeln;
  writeln('10! = ', Fact(10));
  writeln('gcd(48,18) = ', Gcd(48, 18));
  writeln('fib(24) = ', Fibonacci(24));
end.

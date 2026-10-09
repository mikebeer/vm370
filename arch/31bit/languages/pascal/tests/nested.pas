program Nested;
var total: integer;

procedure Outer(n: integer);
var local: integer;

  procedure Inner(k: integer);
  begin
    local := local + k;
    total := total + k;
    if k > 0 then Inner(k - 1);
  end;

begin
  local := 100;
  Inner(n);
  writeln('local = ', local, ' total = ', total);
end;

procedure Swap(var a, b: integer);
var t: integer;
begin
  t := a; a := b; b := t;
end;

var x, y: integer;
begin
  total := 0;
  Outer(4);
  Outer(2);
  x := 1; y := 2;
  Swap(x, y);
  writeln(x, ' ', y);
end.

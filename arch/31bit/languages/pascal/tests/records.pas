program Records;
type
  Point = record
    x, y: integer;
  end;
  Person = record
    name: string;
    age: integer;
    height: real;
    pos: Point;
  end;
  Color = (Red, Green, Blue);
var
  p, q: Person;
  pts: array[1..3] of Point;
  i: integer;
  c: Color;

procedure Show(var pr: Person);
begin
  writeln(pr.name, ' is ', pr.age, ' years old, ', pr.height:0:2, 'm, at (', pr.pos.x, ',', pr.pos.y, ')');
end;

procedure Birthday(var pr: Person);
begin
  pr.age := pr.age + 1;
  with pr do begin
    pos.x := pos.x + 10;
    pos.y := pos.y - 5;
  end;
end;

function Dist2(a, b: Point): integer;
begin
  Dist2 := sqr(a.x - b.x) + sqr(a.y - b.y);
end;

begin
  p.name := 'Alice';
  p.age := 30;
  p.height := 1.68;
  p.pos.x := 3;
  p.pos.y := 4;
  q := p;
  q.name := 'Bob';
  Birthday(q);
  Show(p);
  Show(q);
  for i := 1 to 3 do begin
    pts[i].x := i * i;
    pts[i].y := i + 10;
  end;
  writeln('dist2 = ', Dist2(pts[1], pts[3]));
  c := Green;
  if c = Green then writeln('green') else writeln('not green');
  c := succ(c);
  writeln(ord(c));
end.

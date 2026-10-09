program Pointers;
type
  PNode = ^Node;
  Node = record
    value: integer;
    next: PNode;
  end;
var
  head, p, last: PNode;
  i, sum: integer;

procedure Push(var h: PNode; v: integer);
var n: PNode;
begin
  new(n);
  n^.value := v;
  n^.next := h;
  h := n;
end;

function Length(h: PNode): integer;
var c: integer;
begin
  c := 0;
  while h <> nil do begin
    c := c + 1;
    h := h^.next;
  end;
  Length := c;
end;

begin
  head := nil;
  for i := 1 to 10 do Push(head, i * i);
  p := head;
  sum := 0;
  while p <> nil do begin
    write(p^.value, ' ');
    sum := sum + p^.value;
    p := p^.next;
  end;
  writeln;
  writeln('count = ', Length(head), ' sum = ', sum);
  while head <> nil do begin
    p := head;
    head := head^.next;
    dispose(p);
  end;
  writeln('freed, nil? ', head = nil);
end.

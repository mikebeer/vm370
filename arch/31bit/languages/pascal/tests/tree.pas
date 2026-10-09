program Tree;
type
  PTree = ^TNode;
  TNode = record
    key: integer;
    name: string;
    left, right: PTree;
  end;
var
  root: PTree;
  i: integer;

procedure Insert(var t: PTree; k: integer; nm: string);
begin
  if t = nil then begin
    new(t);
    t^.key := k;
    t^.name := nm;
    t^.left := nil;
    t^.right := nil;
  end
  else if k < t^.key then Insert(t^.left, k, nm)
  else Insert(t^.right, k, nm);
end;

procedure InOrder(t: PTree);
begin
  if t <> nil then begin
    InOrder(t^.left);
    write(t^.key, ':', t^.name, ' ');
    InOrder(t^.right);
  end;
end;

function Height(t: PTree): integer;
var l, r: integer;
begin
  if t = nil then Height := 0
  else begin
    l := Height(t^.left);
    r := Height(t^.right);
    if l > r then Height := l + 1 else Height := r + 1;
  end;
end;

function Find(t: PTree; k: integer): PTree;
begin
  while (t <> nil) and (t^.key <> k) do
    if k < t^.key then t := t^.left else t := t^.right;
  Find := t;
end;

begin
  root := nil;
  for i := 1 to 12 do Insert(root, (i * 37) mod 23, chr(64 + i));
  InOrder(root);
  writeln;
  writeln('height ', Height(root));
  if Find(root, 14) <> nil then writeln('found 14: ', Find(root, 14)^.name);
  if Find(root, 99) = nil then writeln('99 not found');
  with root^ do writeln('root key ', key, ' name ', name);
end.

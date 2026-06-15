#!/usr/bin/env python3
import os
import sys
import re

class GXTCLI:
    def __init__(self, filepath):
        self.filepath = filepath
        self.strings = []
        self.modified = False
        self.backup = None
    
    def is_valid_text(self, text):
        if not text or len(text) < 2:
            return False
        
        valid_chars = re.compile(r'^[A-Za-z0-9áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ\s\.,!?;:\(\)\[\]\{\}\"\'~@#$%&*+\-=<>/\\|]+$')
        
        if not valid_chars.match(text):
            valid_count = sum(1 for c in text if valid_chars.match(c))
            if valid_count < len(text) * 0.8:
                return False
        
        if len(text) < 3:
            return False
        
        if not any(c.isalpha() or c.isspace() for c in text):
            return False
        
        return True
    
    def load(self):
        try:
            with open(self.filepath, 'rb') as f:
                data = f.read()
            
            if data[:2] == b'\xFF\xFE':
                text = data[2:].decode('utf-16-le', errors='ignore')
            else:
                text = data.decode('utf-16-le', errors='ignore')
            
            raw_strings = text.split('\x00')
            
            current_key = None
            for s in raw_strings:
                if not s:
                    continue
                
                if re.match(r'^[A-Z][A-Z0-9_]{1,15}$', s) and len(s) <= 16:
                    current_key = s
                else:
                    if self.is_valid_text(s):
                        key = current_key if current_key else f"TEXT_{len(self.strings)}"
                        clean_text = re.sub(r'[^\w\s\.,!?;:\(\)\[\]\{\}\"\'~@#$%&*+\-=<>/\\|áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', '', s)
                        if clean_text.strip():
                            self.strings.append({
                                'id': len(self.strings),
                                'key': key,
                                'value': clean_text
                            })
                    current_key = None
            
            print(f"\n[OK] Loaded {len(self.strings)} strings from {os.path.basename(self.filepath)}\n")
            return True
            
        except Exception as e:
            print(f"\n[ERR] Failed to load: {e}\n")
            return False
    
    def save(self, output_path=None):
        if not output_path:
            output_path = self.filepath.replace('.gxt', '_modified.gxt')
        
        try:
            all_text = []
            for s in self.strings:
                all_text.append(s['key'])
                all_text.append(s['value'])
            
            final_text = '\x00'.join(all_text) + '\x00\x00'
            new_data = final_text.encode('utf-16-le')
            final_data = b'\xFF\xFE' + new_data
            
            with open(output_path, 'wb') as f:
                f.write(final_data)
            
            self.modified = False
            print(f"\n[OK] Saved to {output_path}\n")
            return True
            
        except Exception as e:
            print(f"\n[ERR] Failed to save: {e}\n")
            return False
    
    def cmd_help(self):
        print("COMMANDS:")
        print("  list [page]            - List strings")
        print("  search <text>          - Search in strings")
        print("  key <key>              - Search by key")
        print("  show <id>              - Show string by ID")
        print("  edit <id> <new text>   - Edit string")
        print("  save                   - Save changes")
        print("  saveas <file>          - Save as")
        print("  export <file>          - Export to TXT")
        print("  stats                  - Show statistics")
        print("  undo                   - Undo last edit")
        print("  reload                 - Reload original file")
        print("  help                   - Show this help")
        print("  quit                   - Exit\n")
    
    def cmd_list(self, pagina=1):
        items_por_pagina = 20
        total = len(self.strings)
        total_paginas = (total + items_por_pagina - 1) // items_por_pagina
        
        if pagina < 1:
            pagina = 1
        if pagina > total_paginas:
            pagina = total_paginas
        
        inicio = (pagina - 1) * items_por_pagina
        fim = inicio + items_por_pagina
        
        
        for s in self.strings[inicio:fim]:
            value_preview = s['value'][:60].replace('\n', ' ')
            print(f"ID: {s['id']} KEY: {s['key']} | Text: {value_preview}{'...' if len(s['value']) > 60 else ''}")
        print(f"\n Page {pagina}/{total_paginas} (Total: {total})")

    def cmd_search(self, termo):
        results = []
        for s in self.strings:
            if termo.lower() in s['value'].lower() or termo.lower() in s['key'].lower():
                results.append(s)
        
        if not results:
            print(f"\n[ERR] No strings found for: {termo}\n")
            return
        
        print(f"{'-'*70}\n")
        
        for s in results[:50]:
            value_preview = s['value'][:60].replace('\n', ' ')
            print(f"ID: {s['id']} | Key: {s['key']} | Text: {value_preview}{'...' if len(s['value']) > 60 else ''}")
        
        if len(results) > 50:
            print(f"... and {len(results) - 50} more results\n")
        print(f"\n \"{termo}\" ({len(results)} found)")
    
    def cmd_key(self, key):
        results = [s for s in self.strings if key.upper() in s['key']]
        
        if not results:
            print(f"\n[ERR] No keys found: {key}\n")
            return
        
        print(f"\n{'-'*70}")
        
        for s in results:
            print(f"ID: {s['id']} | Key: {s['key']} | Text: {s['value'][:50]}...")
        print(f"KEYS FOUND: {key} ({len(results)})")
        print()
    
    def cmd_show(self, id_str):
        try:
            sid = int(id_str)
        except:
            print(f"\n[ERR] Invalid ID: {id_str}\n")
            return
        
        s = next((x for x in self.strings if x['id'] == sid), None)
        if not s:
            print(f"\n[ERR] String ID {sid} not found!\n")
            return
        
        print(f"\n{'-'*70}")
        print(f"ID: {s['id']}  |  KEY: {s['key']}  | Text: {s['value']}\n")
    
    def cmd_edit(self, args):
        if len(args) < 2:
            print("\n[ERR] Usage: edit <id> <new text>\n")
            return
        
        try:
            sid = int(args[0])
            novo_texto = ' '.join(args[1:])
        except:
            print("\n[ERR] Invalid ID!\n")
            return
        
        s = next((x for x in self.strings if x['id'] == sid), None)
        if not s:
            print(f"\n[ERR] String ID {sid} not found!\n")
            return
        
        old = s['value']
        s['value'] = novo_texto
        self.modified = True
        
        print(f"\n[OK] String {sid} changed!")
        print(f"   BEFORE: {old[:60]}...")
        print(f"   AFTER:  {novo_texto[:60]}...\n")
    
    def cmd_undo(self):
        if self.backup is None:
            print("\n[ERR] Nothing to undo\n")
            return
        
        self.strings = [s.copy() for s in self.backup]
        self.modified = True
        self.backup = None
        print("\n[OK] Last edit undone!\n")
    
    def cmd_reload(self):
        self.load()
        self.modified = False
        self.backup = None
        print("\n[OK] File reloaded!\n")
    
    def cmd_stats(self):
        total = len(self.strings)
        total_chars = sum(len(s['value']) for s in self.strings)
        avg_len = total_chars // total if total > 0 else 0
        
        print(f"\n{'-'*70}\n")
        print(f"- STATISTICS")
        print(f"  File: {os.path.basename(self.filepath)}")
        print(f"  Total strings: {total}")
        print(f"  Total characters: {total_chars}")
        print(f"  Average length: {avg_len}")
        print(f"  Modified: {'Yes' if self.modified else 'No'}")
    
    def cmd_export(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for s in self.strings:
                    f.write(f"{s['id']} {s['key']}\n")
                    f.write(f"{s['value']}\n")
                    f.write("-" * 70 + "\n")
            print(f"\n[OK] Exported to: {filename}\n")
        except Exception as e:
            print(f"\n[ERR] Export failed: {e}\n")
    
    def run(self):
        if not self.load():
            return
        
        print("Type 'help' for commands\n")
        
        while True:
            try:
                cmd = input("gxt> ").strip()
                if not cmd:
                    continue
                
                partes = cmd.split()
                comando = partes[0].lower()
                args = partes[1:]
                
                if comando in ['quit', 'exit', 'q']:
                    if self.modified:
                        resp = input("\n[WARN] Unsaved changes. Save before exit? (y/N): ")
                        if resp.lower() == 'y':
                            self.save()
                    print("\n[OK] Goodbye\n")
                    break
                
                elif comando == 'help':
                    self.cmd_help()
                
                elif comando == 'list':
                    pagina = int(args[0]) if args and args[0].isdigit() else 1
                    self.cmd_list(pagina)
                
                elif comando == 'search':
                    if not args:
                        print("\n[ERR] Usage: search <text>\n")
                    else:
                        self.cmd_search(' '.join(args))
                
                elif comando == 'key':
                    if not args:
                        print("\n[ERR] Usage: key <key>\n")
                    else:
                        self.cmd_key(args[0])
                
                elif comando == 'show':
                    if not args:
                        print("\n[ERR] Usage: show <id>\n")
                    else:
                        self.cmd_show(args[0])
                
                elif comando == 'edit':
                    if len(args) < 2:
                        print("\n[ERR] Usage: edit <id> <new text>\n")
                    else:
                        self.backup = [s.copy() for s in self.strings]
                        self.cmd_edit(args)
                
                elif comando == 'save':
                    self.save()
                
                elif comando == 'saveas':
                    if not args:
                        print("\n[ERR] Usage: saveas <file.gxt>\n")
                    else:
                        self.save(args[0])
                
                elif comando == 'export':
                    if not args:
                        print("\n[ERR] Usage: export <file.txt>\n")
                    else:
                        self.cmd_export(args[0])
                
                elif comando == 'undo':
                    self.cmd_undo()
                
                elif comando == 'reload':
                    self.cmd_reload()
                
                elif comando == 'stats':
                    self.cmd_stats()
                
                else:
                    print(f"\n[ERR] Unknown command: {comando}\n")
                    print("Type 'help' for commands\n")
                    
            except KeyboardInterrupt:
                print("\n")
                continue
            except EOFError:
                break

def main():
    if len(sys.argv) < 2:
        print("\nGXT Editor CLI - Interactive Mode\n")
        print("Usage: python gxt_cli.py <file.gxt>\n")
        print("Example: python gxt_cli.py pc_game.gxt\n")
        sys.exit(1)
    
    if not os.path.exists(sys.argv[1]):
        print(f"\n[ERR] File not found: {sys.argv[1]}\n")
        sys.exit(1)
    
    app = GXTCLI(sys.argv[1])
    app.run()

if __name__ == "__main__":
    main()
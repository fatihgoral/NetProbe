import json, os

log_file = r'C:\Users\Eren\.gemini\antigravity\brain\022c3c2c-667c-4847-b95b-1fd3d4c11aad\.system_generated\logs\transcript.jsonl'

with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('source') == 'MODEL' and 'tool_calls' in data:
            for call in data['tool_calls']:
                args = call.get('args', {})
                if type(args) != dict: continue
                target_file = args.get('TargetFile')
                if not target_file: continue
                if type(target_file) == str and target_file.startswith('"'):
                    target_file = target_file.strip('"').encode('utf-8').decode('unicode_escape')
                if not target_file.startswith(r'C:\Users\Eren\Desktop\NetProbe'): continue
                
                if call['name'] == 'write_to_file':
                    print('Writing', target_file)
                    content = args.get('CodeContent', '')
                    if type(content) == str and content.startswith('"'):
                        content = content.strip('"').encode('utf-8').decode('unicode_escape')
                    with open(target_file, 'w', encoding='utf-8') as tf: tf.write(content)
                        
                elif call['name'] == 'replace_file_content':
                    print('Replace in', target_file)
                    target_content = args.get('TargetContent', '')
                    rep_content = args.get('ReplacementContent', '')
                    if type(target_content) == str and target_content.startswith('"'):
                        target_content = target_content.strip('"').encode('utf-8').decode('unicode_escape')
                    if type(rep_content) == str and rep_content.startswith('"'):
                        rep_content = rep_content.strip('"').encode('utf-8').decode('unicode_escape')
                    with open(target_file, 'r', encoding='utf-8') as tf: text = tf.read()<truncated 1477 bytes>
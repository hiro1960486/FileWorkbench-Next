"""Pure rename planning. No file is changed by building a plan."""
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import re
from ..core.safety import validate_name,key,unique_planned

@dataclass
class RenameRules:
    find:str=''
    replacement:str=''
    prefix:str=''
    suffix:str=''
    regex:bool=False
    case_sensitive:bool=True
    trim:bool=False
    letter_case:str='keep'
    extension:str=''
    extension_filter:str=''
    numbering:bool=False
    start:int=1
    digits:int=3
    number_position:str='prefix'
    delimiter:str='_'
    date_source:str='none'
    date_format:str='%Y%m%d'
    date_position:str='prefix'


def build_plan(paths,rules):
    files=sorted([Path(p) for p in paths],key=lambda p:str(p).casefold())
    reserved={key(p) for p in files};rows=[];number=rules.start
    extensions={e.strip().lower().lstrip('.') for e in rules.extension_filter.split(',') if e.strip()}
    for path in files:
        try:
            if extensions and path.suffix.lower().lstrip('.') not in extensions:rows.append((path,path,'対象外'));continue
            stem=path.stem
            if rules.trim:stem=stem.strip()
            if rules.find:
                if rules.regex or not rules.case_sensitive:
                    pattern=rules.find if rules.regex else re.escape(rules.find)
                    replacement=rules.replacement if rules.regex else lambda match:rules.replacement
                    stem=re.sub(pattern,replacement,stem,flags=0 if rules.case_sensitive else re.IGNORECASE)
                else:stem=stem.replace(rules.find,rules.replacement)
            if rules.letter_case=='lower':stem=stem.lower()
            elif rules.letter_case=='upper':stem=stem.upper()
            elif rules.letter_case=='title':stem=stem.title()
            stem=rules.prefix+stem+rules.suffix
            if rules.numbering:
                serial=str(number).zfill(rules.digits);number+=1
                stem=serial+rules.delimiter+stem if rules.number_position=='prefix' else stem+rules.delimiter+serial
            if rules.date_source!='none':
                stat=path.stat();timestamp=stat.st_mtime if rules.date_source=='modified' else getattr(stat,'st_birthtime',stat.st_ctime) if rules.date_source=='created' else datetime.now().timestamp()
                date=datetime.fromtimestamp(timestamp).strftime(rules.date_format)
                stem=date+rules.delimiter+stem if rules.date_position=='prefix' else stem+rules.delimiter+date
            extension='.'+rules.extension.lstrip('.') if rules.extension else path.suffix
            target=path.with_name(stem+extension);validate_name(target.name)
            status='変更なし' if target==path else 'OK'
            if key(target)!=key(path) and (target.exists() or key(target) in reserved):target=unique_planned(target,reserved);status='自動回避'
            reserved.add(key(target));rows.append((path,target,status))
        except Exception as exc:rows.append((path,path,'無効: '+str(exc)))
    return rows

"Adapted from https://github.com/ankitpopli1891/django-autotranslate/"

from deep_translator import GoogleTranslator
import polib
import re
import sys
  
def translate_po_file(po_file_path, target_language):
    po = polib.pofile(po_file_path)
    strings = get_strings_to_translate(po)
    translator = GoogleTranslator(source='auto', target=target_language)
    translated_strings = [translator.translate(string) if translator.translate(string) is not None else string for string in strings]
    update_translations(po, translated_strings)
    po.save(po_file_path)
    
def need_translate(entry):
        return not entry.obsolete
    
def humanize_placeholders(msgid):
    return re.sub(
        r'%(?:\((\w+)\))?([sd])',
        lambda match: r'__{0}__'.format(
            match.group(1).lower() if match.group(1) else 'number' if match.group(2) == 'd' else 'item'),
        msgid)

def get_strings_to_translate(po):
    strings = []
    for index, entry in enumerate(po):
        # If it doesn't need translation, go to next one
        if not need_translate(entry):
            continue
        #strings.append(humanize_placeholders(entry.msgid))
        strings.append(entry.msgid)
        # If there is also a plural form, also translate that
        if entry.msgid_plural:
            strings.append(humanize_placeholders(entry.msgid_plural))
    return strings

def restore_placeholders(msgid, translation):
    """Restore placeholders in the translated message."""
    placehoders = re.findall(r'(\s*)(%(?:\(\w+\))?[sd])(\s*)', msgid)
    return re.sub(
        r'(\s*)(__[\w]+?__)(\s*)',
        lambda matches: '{0}{1}{2}'.format(placehoders[0][0], placehoders[0][1], placehoders.pop(0)[2]),
        translation)

def fix_translation(msgid, translation):
    # Google Translate removes a lot of formatting, these are the fixes:
    # - Add newline in the beginning if msgid also has that
    if msgid.startswith('\n') and not translation.startswith('\n'):
        translation = u'\n' + translation

    # - Add newline at the end if msgid also has that
    if msgid.endswith('\n') and not translation.endswith('\n'):
        translation += u'\n'

    # Remove spaces that have been placed between %(id) tags
    try:
        translation = restore_placeholders(msgid, translation)
    except:
        pass
    return translation

def update_translations(entries, translated_strings):
    translations = iter(translated_strings)
    for entry in entries:
        if not need_translate(entry):
            continue
            
        if entry.msgid_plural:
            # fill the first plural form with the entry.msgid translation
            translation = next(translations)
            #translation = fix_translation(entry.msgid, translation)
            entry.msgstr_plural[0] = translation

            # fill the rest of plural forms with the entry.msgid_plural translation
            translation = next(translations)
            translation = fix_translation(entry.msgid_plural, translation)
            for k, v in entry.msgstr_plural.items():
                if k != 0:
                    entry.msgstr_plural[k] = translation
        else:
            translation = next(translations)
            translation = fix_translation(entry.msgid, translation)
            entry.msgstr = translation  
       
    
if __name__=="__main__":
    po_file_path = sys.argv[1]
    target_language = sys.argv[2]
    translate_po_file(po_file_path, target_language)

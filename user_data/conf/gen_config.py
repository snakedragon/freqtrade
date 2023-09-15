from jinja2 import Template as tpl
from pathlib import Path


class JinjaConfigGenerator:

    

    def __init__(self, template_path, output_path, **kwargs):
        self.template_path = template_path
        self.output_path = output_path
        self.kwargs = kwargs

    def generate(self, data: dict):
        template = tpl(Path(self.template_path).read_text())
        output = template.render(**data)
        Path(self.output_path).write_text(output)


def synthesize_conf(
                    seqNo: int, 
                    indicator_data: dict, 
                    entry_signal_data:dict, 
                    extract_signal_data:dict, 
                    output_path: str):
    config_data = {
        "exchange": {
            "name": "gateio",
            "key": "2d5f870ea0af5c1b0d3cb60c9c2cfe81",
            "secret": "f1441dc61ceed5ba24eb4082e7153b467d7990cc2e328ce812e27c1a9430fe6f"
        },
        "stake_amount": 50,
        "seqNo": seqNo,
        "port": 8080+seqNo,
        "indicator_data" : {},
        "entry_signal_data": {},
        "extract_signal_data": {}
    }

    tpl_path  = 'user_data/conf/tpl/config_json.tpl'
    
    config_data['indicator_data'].update(indicator_data)
    config_data['entry_signal_data'].update(entry_signal_data)
    config_data['extract_signal_data'].update(extract_signal_data)

    generator = JinjaConfigGenerator(tpl_path, output_path)
    generator.generate(data=config_data)


if __name__ == '__main__':
    from itertools import product, permutations, combinations
    indicator_data = {}
    entry_signal_data = {}
    extract_signal_data = {}

    for n in range(0,60):
        output_path = f'user_data/conf/config_{n}.json'
        synthesize_conf(n,indicator_data,entry_signal_data,extract_signal_data,output_path)
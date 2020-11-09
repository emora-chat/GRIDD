# default_params = {
#     'mention_id': [BaseMentionIdentification()],
#     'node_merge': [BaseNodeMerge()],
#     'inference': [BaseInference()],
#     'response_select': [BaseResponseSelection()],
#     'response_expand': [BaseResponseExpansion()],
#     'response_gen': [BaseResponseGeneration()]
# }
#
#
# default_params = {
#     'mention_id': {
#         BaseMentionIdentification(): {
#             'weight': 1.0
#         },
#         AnotherModel(): {
#             'weight': 2.0
#         }
#     }
# }
#
# # todo - turn mention_mappings into exclusive-or relationship between hypotheses
# # todo - add to dialogue_graph
#
# asr_hypotheses = [
#     {'text': 'bob loves sally',
#      'text_confidence': 0.87,
#      'tokens': ['bob', 'loves', 'sally'],
#      'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80}
#      },
#     {'text': 'bob loves silly',
#      'text_confidence': 0.80,
#      'tokens': ['bob', 'loves', 'silly'],
#      'token_confidence': {0: 0.90, 1: 0.90, 2: 0.60}
#      }
# ]
#
# dialogue_graph = None  # todo - initialize new Dialogue Semantic Graph
# framework = Framework(default_params)
# framework.process_utterance(asr_hypotheses, dialogue_graph)
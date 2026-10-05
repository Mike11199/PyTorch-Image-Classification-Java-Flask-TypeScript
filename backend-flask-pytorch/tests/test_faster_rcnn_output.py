import json
import unittest

import torch

from images.boxes import output_fn


class FasterRcnnOutputTests(unittest.TestCase):
    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA regression')
    def test_serializes_cuda_predictions(self):
        prediction = [{
            'scores': torch.tensor([0.95], device='cuda'),
            'boxes': torch.tensor([[1.0, 2.0, 11.0, 22.0]], device='cuda'),
            'labels': torch.tensor([3], device='cuda'),
        }]

        result = json.loads(output_fn(prediction))

        self.assertEqual(result['boxes'], [[1, 2, 11, 22]])
        self.assertEqual(result['labels'], [3])
        self.assertEqual(result['classes'], ['car'])


if __name__ == '__main__':
    unittest.main()

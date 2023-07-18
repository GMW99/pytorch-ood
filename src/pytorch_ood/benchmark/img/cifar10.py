"""

"""
from typing import Dict, List

from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import CIFAR10

from pytorch_ood.api import Detector
from pytorch_ood.dataset.img import LSUNCrop, LSUNResize, TinyImageNetCrop, TinyImageNetResize, GaussianNoise, UniformNoise
from pytorch_ood.utils import OODMetrics, ToUnknown
from pytorch_ood.benchmark import Benchmark


class CIFAR10_ODIN(Benchmark):
    """
    Replicates the OOD detection benchmark from the ODIN paper for CIFAR 10.

    :see Paper: `ArXiv <https://arxiv.org/abs/1706.02690>`__

    Outlier datasets are

     * TinyImageNetCrop
     * TinyImageNetResize
     * LSUNResize
     * LSUNCrop
     * Uniform
     * Gaussian
    """

    def __init__(self, root, transform):
        """
        :param root: where to store datasets
        :param transform: transform to apply to images
        """
        self.transform = transform
        self.train_in = CIFAR10(root, download=True, transform=transform, train=True)
        self.test_in = CIFAR10(root, download=True, transform=transform, train=False)

        self.test_oods = [
            TinyImageNetCrop(
                root, download=True, transform=transform, target_transform=ToUnknown()
            ),
            TinyImageNetResize(
                root, download=True, transform=transform, target_transform=ToUnknown()
            ),
            LSUNResize(
                root, download=True, transform=transform, target_transform=ToUnknown()
            ),
            LSUNCrop(
                root, download=True, transform=transform, target_transform=ToUnknown()
            ),
            UniformNoise(1000, size=(32, 32, 3), transform=transform, target_transform=ToUnknown(), seed=123),
            GaussianNoise(1000, size=(32, 32, 3), transform=transform, target_transform=ToUnknown(), seed=123)
        ]

        self.ood_names: List[str] = []  #: OOD Dataset names
        self.ood_names = ["TinyImageNetCrop", "TinyImageNetResize", "LSUNResize", "LSUNCrop", "Uniform", "Gaussian"]

    def train_set(self) -> Dataset:
        """
        Training dataset
        """
        return self.train_in

    def test_sets(self, known=True, unknown=True) -> List[Dataset]:
        """
        List of the different test datasets.
        If known and unknown are true, each dataset contains IN and OOD data.

        :param known: include IN
        :param unknown: include OOD
        """

        if known and unknown:
            return [self.test_in + other for other in self.test_oods]

        if known and not unknown:
            return [self.train_in]

        if not known and unknown:
            return self.ood_datasets

        raise ValueError()

    def evaluate(
        self, detector: Detector, loader_kwargs: Dict = None, device: str = "cpu"
    ) -> List[Dict]:
        """
        Evaluates the given detector on all datasets and returns a list with the results

        :param detector: the detector to evaluate
        :param loader_kwargs: keyword arguments to give to the data loader
        :param device: the device to move batches to
        """
        if loader_kwargs is None:
            loader_kwargs = {}

        metrics = []

        for name, dataset in zip(self.ood_names, self.test_sets()):
            loader = DataLoader(dataset=dataset, **loader_kwargs)

            m = OODMetrics()

            for x, y in loader:
                m.update(detector(x.to(device)), y)

            r = m.compute()
            r.update({"Dataset": name})

            metrics.append(r)

        return metrics
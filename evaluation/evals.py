# Has to implement different eval metrics like accuracy, execution time before after and pruning model

import numpy as np
import torch


def correct(output, target, topk=(1,)):
    """Computes how many correct outputs with respect to targets

    Does NOT compute accuracy but just a raw amount of correct
    outputs given target labels. This is done for each value in
    topk. A value is considered correct if target is in the topk
    highest values of output.
    The values returned are upperbounded by the given batch size

    [description]

    Arguments:
        output {torch.Tensor} -- Output prediction of the model
        target {torch.Tensor} -- Target labels from data

    Keyword Arguments:
        topk {iterable} -- [Iterable of values of k to consider as correct] (default: {(1,)})

    Returns:
        List(int) -- Number of correct values for each topk
    """

    with torch.no_grad():
        maxk = max(topk)
        # Only need to do topk for highest k, reuse for the rest
        _, pred = output.topk(k=maxk, dim=1, largest=True, sorted=True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
            res.append(correct_k.item())
        return res


def accuracy(model, dataloader, topk=(1,)):
    """Compute accuracy of a model over a dataloader for various topk

    Arguments:
        model {torch.nn.Module} -- Network to evaluate
        dataloader {torch.utils.data.DataLoader} -- Data to iterate over

    Keyword Arguments:
        topk {iterable} -- [Iterable of values of k to consider as correct] (default: {(1,)})

    Returns:
        List(float) -- List of accuracies for each topk
    """

    # Use same device as model
    device = next(model.parameters()).device

    accs = np.zeros(len(topk))
    with torch.no_grad():
        for i, (input, target) in enumerate(dataloader):
            input = input.to(device)
            target = target.to(device)
            output = model(input)
            accs += np.array(correct(output, target, topk))

    # Normalize over data length
    accs /= len(dataloader.dataset)

    return 100*accs


# def weights_sum(model):
#     total = 0
#     for name, module in model.named_modules():
#         if isinstance(module, torch.nn.Conv2d) or isinstance(module, torch.nn.Linear):
#             flatten_weight_array = torch.flatten(module.weight)
#             total += torch.sum(flatten_weight_array).item()
#     return total

def non_zero_weights(model):
    total = 0
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d) or isinstance(module, torch.nn.Linear):
            flatten_weight_array = torch.flatten(module.weight)
            nz_tuple = torch.nonzero(flatten_weight_array, as_tuple=True)
            nz_elements = nz_tuple[0].size()[0]
            total += nz_elements
    return total


def compression_ratio(model, pruned_model):
    return non_zero_weights(pruned_model) / non_zero_weights(model)

# Will add a new function to count flops

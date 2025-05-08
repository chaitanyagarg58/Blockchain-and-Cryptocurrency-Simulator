// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IDEX {
    function spotPrice() external view returns (uint256, uint256); // returns (reserveA, reserveB)
    function swap(address inputToken, address outputToken, uint256 inputAmount) external;
    function tokenA() external view returns (IERC20);
    function tokenB() external view returns (IERC20);
}

contract Arbitrageur is Ownable {
    IDEX public dex1;
    IDEX public dex2;
    uint256 public fee = 30; // 0.3% = 30/10000
    uint256 public minProfitThreshold = 5; // 0.05% = 5/10000

    event ArbitrageOpportunity(string direction, IDEX dex1, IDEX dex2, uint256 amount);

    constructor(address _dex1, address _dex2) Ownable(msg.sender) {
        require(_dex1 != address(0) && _dex2 != address(0), "DEX addresses cannot be zero");
        dex1 = IDEX(_dex1);
        dex2 = IDEX(_dex2);
    }

    function detectArbitrageA_B_A(uint256 amount, IDEX _dex1, IDEX _dex2) internal view returns (uint256) {
        require(amount > 0, "Amount must be greater than zero");

        (uint256 reserveA1, uint256 reserveB1) = _dex1.spotPrice();
        (uint256 reserveA2, uint256 reserveB2) = _dex2.spotPrice();

        require(reserveA1 > 0 && reserveB1 > 0 && reserveA2 > 0 && reserveB2 > 0, "Invalid reserves");

        uint256 fee1 = (amount * fee) / 10000;
        uint256 amount2 = reserveB1 - (reserveA1 * reserveB1) / (reserveA1 + amount - fee1);

        uint256 fee2 = (amount2 * fee) / 10000;
        uint256 amountFinal = reserveA2 - (reserveB2 * reserveA2) / (reserveB2 + amount2 - fee2);

        if (amountFinal <= amount || amountFinal - amount < ((amount * minProfitThreshold) / 10000)) {
            return 0;
        }
        return amountFinal - amount;
    }

    function detectArbitrageB_A_B(uint256 amount, IDEX _dex1, IDEX _dex2) internal view returns (uint256) {
        require(amount > 0, "Amount must be greater than zero");

        (uint256 reserveA1, uint256 reserveB1) = _dex1.spotPrice();
        (uint256 reserveA2, uint256 reserveB2) = _dex2.spotPrice();
        
        require(reserveA1 > 0 && reserveB1 > 0 && reserveA2 > 0 && reserveB2 > 0, "Invalid reserves");

        uint256 fee1 = (amount * fee) / 10000;
        uint256 amount2 = reserveA1 - (reserveB1 * reserveA1) / (reserveB1 + amount - fee1);

        uint256 fee2 = (amount2 * fee) / 10000;
        uint256 amountFinal = reserveB2 - (reserveA2 * reserveB2) / (reserveA2 + amount2 - fee2);

        if (amountFinal <= amount || amountFinal - amount < ((amount * minProfitThreshold) / 10000)) {
            return 0;
        }
        return amountFinal - amount;
    }

    function executeArbitrage(IERC20 tokenA, IERC20 tokenB, IDEX _dex1, IDEX _dex2, uint256 amountIn) internal {
        require(amountIn > 0, "Amount must be greater than zero");
        require(tokenA.balanceOf(owner()) >= amountIn, "Insufficient Token A balance");

        // Transfer A to this contract
        tokenA.transferFrom(address(owner()), address(this), amountIn);

        // Swap A -> B on _dex1
        tokenA.approve(address(_dex1), amountIn);
        _dex1.swap(address(tokenA), address(tokenB), amountIn);
        uint256 amountBReceived = tokenB.balanceOf(address(this));

        require(amountBReceived > 0, "Swap A->B failed");

        // Swap B -> A on _dex2
        tokenB.approve(address(_dex2), amountBReceived);
        _dex2.swap(address(tokenB), address(tokenA), amountBReceived);
        uint256 amountAReceived = tokenA.balanceOf(address(this));

        // Transfer A back to owner
        tokenA.transfer(address(owner()), amountAReceived);
    }

    function helper1() internal returns (bool) {
        IERC20 tokenA = dex1.tokenA();
        IERC20 tokenB = dex1.tokenB();
        require(address(tokenA) != address(0) && address(tokenB) != address(0), "Invalid token addresses");

        (uint256 reserveA1, uint256 reserveB1) = dex1.spotPrice();
        (uint256 reserveA2, uint256 reserveB2) = dex2.spotPrice();

        uint256 amountA = tokenA.balanceOf(address(owner()));
        uint256 amountB = tokenB.balanceOf(address(owner()));

        // A -> B -> A, dex1 -> dex2
        uint256 amountInA_B_A_1_2 = amountA > reserveA1 / 100 ? reserveA1 / 100 : amountA;
        uint256 profitA_B_A_1_2 = detectArbitrageA_B_A(amountInA_B_A_1_2, dex1, dex2);

        // B -> A -> B, dex2 -> dex1
        uint256 amountInB_A_B_2_1 = amountB > reserveB2 / 100 ? reserveB2 / 100 : amountB;
        uint256 profitB_A_B_2_1 = detectArbitrageB_A_B(amountInB_A_B_2_1, dex2, dex1);

        if (profitA_B_A_1_2 != 0 || profitB_A_B_2_1 != 0) {
            if (profitA_B_A_1_2 * (reserveB1 + reserveB2) > profitB_A_B_2_1 * (reserveA1 + reserveA2) ) {
                executeArbitrage(tokenA, tokenB, dex1, dex2, amountInA_B_A_1_2);
            }
            else {
                executeArbitrage(tokenB, tokenA, dex2, dex1, amountInB_A_B_2_1);
            }
            return true;
        }
        else return false;
    }

    function helper2() internal returns (bool) {
        IERC20 tokenA = dex1.tokenA();
        IERC20 tokenB = dex1.tokenB();
        require(address(tokenA) != address(0) && address(tokenB) != address(0), "Invalid token addresses");

        (uint256 reserveA1, uint256 reserveB1) = dex1.spotPrice();
        (uint256 reserveA2, uint256 reserveB2) = dex2.spotPrice();

        uint256 amountA = tokenA.balanceOf(address(owner()));
        uint256 amountB = tokenB.balanceOf(address(owner()));

        // A -> B -> A, dex2 -> dex1
        uint256 amountInA_B_A_2_1 = amountA > reserveA2 / 100 ? reserveA2 / 100 : amountA;
        uint256 profitA_B_A_2_1 = detectArbitrageA_B_A(amountInA_B_A_2_1, dex2, dex1);

        // B -> A -> B, dex1 -> dex2
        uint256 amountInB_A_B_1_2 = amountB > reserveB1 / 100 ? reserveB1 / 100 : amountB;
        uint256 profitB_A_B_1_2 = detectArbitrageB_A_B(amountInB_A_B_1_2, dex1, dex2);

        if (profitA_B_A_2_1 > 0 || profitB_A_B_1_2 > 0) {
            if (profitA_B_A_2_1 * (reserveB1 + reserveB2) > profitB_A_B_1_2 * (reserveA1 + reserveA2) ) {
                executeArbitrage(tokenA, tokenB, dex2, dex1, amountInA_B_A_2_1);
            }
            else {
                executeArbitrage(tokenB, tokenA, dex1, dex2, amountInB_A_B_1_2);
            }
            return true;
        }
        else return false;
    }

    function calculateAndExecuteArbitrage() external onlyOwner {
        if (helper1()) return;
        else if (helper2()) return;
        else revert("No arbitrage opportunity found");
    }

    function updateMinProfitThreshold(uint256 newThreshold) external onlyOwner {
        minProfitThreshold = newThreshold;
    }
}
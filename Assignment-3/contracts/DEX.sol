// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "./LPToken.sol";

using EnumerableSet for EnumerableSet.AddressSet;

contract DEX {
    IERC20 public tokenA;
    IERC20 public tokenB;
    LPToken public lpToken;

    uint256 public reserveA = 0;
    uint256 public reserveB = 0;
    
    uint256 public fee = 30; // 0.3% swap fee, e.g., 30/10000

    EnumerableSet.AddressSet private liquidityProviders;
    mapping(address => uint256) public lpFeeBalanceA;
    uint256 public totalLpFeeBalanceA = 0;
    mapping(address => uint256) public lpFeeBalanceB;
    uint256 public totalLpFeeBalanceB = 0;

    bool internal lpWithdrawalLock = false;

    uint256 public totalSwappedA = 0;
    uint256 public totalSwappedB = 0;
    uint256 public totalLpFeeCollectedA = 0;
    uint256 public totalLpFeeCollectedB = 0;

    modifier noReentranct() {
        require(!lpWithdrawalLock, "Reentrant call");
        lpWithdrawalLock = true;
        _;
        lpWithdrawalLock = false;
    }

    constructor(address _tokenA, address _tokenB) {
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);

        lpToken = new LPToken();
    }

    // Update reserves when liquidity is added
    function updateReserves() internal {
        reserveA = tokenA.balanceOf(address(this)) - totalLpFeeBalanceA;
        reserveB = tokenB.balanceOf(address(this)) - totalLpFeeBalanceB;
    }

    // Function to add liquidity to the pool
    function addLiquidity(uint256 amountA, uint256 amountB) external {
        require(amountA > 0 && amountB > 0, "Invalid amounts");
        
        updateReserves(); // Update reserves before adding liquidity

        if (reserveA == 0 || reserveB == 0) {
            // First LP sets the ratio, mint initial LP tokens
            tokenA.transferFrom(msg.sender, address(this), amountA);
            tokenB.transferFrom(msg.sender, address(this), amountB);

            uint256 lpAmount = sqrt(amountA * amountB); // Fair starting point
            lpToken.mint(msg.sender, lpAmount);
        }
        else {
            // Enforce correct ratio
            uint256 expectedB = (amountA * reserveB) / reserveA;
            require(((amountB > expectedB) && ((amountB - expectedB) < 100)) || ((amountB <= expectedB) && ((expectedB - amountB) < 100)), "Wrong ratio");

            tokenA.transferFrom(msg.sender, address(this), amountA);
            tokenB.transferFrom(msg.sender, address(this), amountB);

            // Mint LP proportional to the pool
            uint256 lpSupply = lpToken.totalSupply();
            uint256 lpAmount = (amountA * lpSupply) / reserveA;
            lpToken.mint(msg.sender, lpAmount);
        }

        liquidityProviders.add(msg.sender);
        
        updateReserves(); // Update reserves after adding liquidity
    }

    // Function for LP to withdraw liquidity
    function removeLiquidity(uint256 lpAmount) external noReentranct {
        // Ensure the LP has enough tokens to burn
        require(lpAmount > 0, "Invalid LP amount");
        require(lpToken.balanceOf(msg.sender) >= lpAmount, "Insufficient LP tokens");
        
        updateReserves(); // Update reserves before removing liquidity

        // Calculate the amount of TokenA and TokenB the LP is entitled to
        uint256 amountA = (lpAmount * reserveA) / lpToken.totalSupply();
        uint256 amountB = (lpAmount * reserveB) / lpToken.totalSupply();

        uint256 feeAmountA = lpFeeBalanceA[msg.sender];
        uint256 feeAmountB = lpFeeBalanceB[msg.sender];

        // Burn the LP tokens
        lpToken.burn(msg.sender, lpAmount);

        // Transfer the corresponding amount of TokenA and TokenB to the LP
        tokenA.transfer(msg.sender, amountA + feeAmountA);
        tokenB.transfer(msg.sender, amountB + feeAmountB);
        lpFeeBalanceA[msg.sender] = 0; // Reset fee balance A
        lpFeeBalanceB[msg.sender] = 0; // Reset fee balance B
        totalLpFeeBalanceA -= feeAmountA; // Update total fee balance A
        totalLpFeeBalanceB -= feeAmountB; // Update total fee balance B

        // Remove the LP from the set if they have no more LP tokens
        if (lpToken.balanceOf(msg.sender) == 0) {
            liquidityProviders.remove(msg.sender);
        }

        updateReserves(); // Update reserves after removing liquidity
    }

    function getReserve(address token) external view returns (uint256) {
        if (token == address(tokenA)) {
            return reserveA;
        } else if (token == address(tokenB)) {
            return reserveB;
        } else {
            revert("Invalid token");
        }
    }

    // Function to get the current reserves
    function spotPrice() public view returns (uint256, uint256) {
        return (reserveA, reserveB);
    }

    // Function to calculate the spot price of TokenA in terms of TokenB
    function getSpotPriceAtoB() public view returns (uint256) {
        require(reserveB > 0, "Invalid reserveB");
        return (reserveA * 1000000) / reserveB;
    }

    // Function to calculate the spot price of TokenB in terms of TokenA
    function getSpotPriceBtoA() public view returns (uint256) {
        require(reserveA > 0, "Invalid reserveA");
        return (reserveB * 1000000) / reserveA;
    }

    function distributeFee(address inputToken, uint256 feeAmount) internal {
        uint256 totalLP = lpToken.totalSupply();

        for (uint256 i = 0; i < liquidityProviders.length(); i++) {
            address provider = liquidityProviders.at(i);
            uint256 lpShare = lpToken.balanceOf(provider);
            uint256 feeShare = (feeAmount * lpShare) / totalLP;
            if (inputToken == address(tokenA)) {
                lpFeeBalanceA[provider] += feeShare;
                totalLpFeeBalanceA += feeShare;
            }
            else if (inputToken == address(tokenB)) {
                lpFeeBalanceB[provider] += feeShare;
                totalLpFeeBalanceB += feeShare;
            }
        }
    }

    function get_swaps_vol() external view returns (uint256, uint256) {
        return (totalSwappedA, totalSwappedB);
    }

    function get_total_fees() external view returns (uint256, uint256) {
        return (totalLpFeeCollectedA, totalLpFeeCollectedB);
    }


    function swap(address inputToken, address outputToken, uint256 inputAmount) external {
        require(inputToken == address(tokenA) || inputToken == address(tokenB), "Invalid input token");
        require(outputToken == address(tokenA) || outputToken == address(tokenB), "Invalid output token");
        require(inputToken != outputToken, "Tokens must be different");
        require(inputAmount > 0, "Invalid input amount");

        updateReserves(); // Update reserves before swap

        require(reserveA > 0 && reserveB > 0, "Insufficient liquidity");

        IERC20 input = IERC20(inputToken);
        IERC20 output = IERC20(outputToken);
        
        require(input.balanceOf(msg.sender) >= inputAmount, "Insufficient balance");

        uint256 inputReserve = (inputToken == address(tokenA)) ? reserveA : reserveB;
        uint256 outputReserve = (outputToken == address(tokenA)) ? reserveA : reserveB;

        // Apply swap fee (0.3%)
        uint256 feeAmount = (inputAmount * fee) / 10000;

        uint256 outputAmount = outputReserve - (inputReserve * outputReserve) / (inputReserve + inputAmount - feeAmount);

        require(outputReserve >= outputAmount, "Insufficient liquidity");

        // Transfer tokens
        input.transferFrom(msg.sender, address(this), inputAmount);
        output.transfer(msg.sender, outputAmount);
        distributeFee(inputToken, feeAmount);

        if (inputToken == address(tokenA)) {
            totalSwappedA += inputAmount;
            totalLpFeeCollectedA += feeAmount;
        } else {
            totalSwappedB += inputAmount;
            totalLpFeeCollectedB += feeAmount;
        }

        updateReserves(); // Update reserves after swap
    }

    function sqrt(uint256 x) internal pure returns (uint256 y) {
        // Babylonian method
        y = x;
        uint256 z = (x + 1) / 2;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }
}
